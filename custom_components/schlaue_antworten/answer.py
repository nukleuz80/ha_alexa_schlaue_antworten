"""Answer core of Schlaue Antworten: build the prompt, ask the AI, clean the reply.

This module knows nothing about how the answer is spoken. Alexa Media, the own
Alexa skill and later an Assist agent all use the same AnswerEngine.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import logging
import re
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    CODEWORD_UNVERSTAENDLICH,
    CONF_ANNOUNCE_MODEL,
    CONF_CUSTOM_KNOWLEDGE,
    CONF_ENABLE_HA_CONTEXT,
    CONF_FALLBACK_AGENT,
    CONF_PRIMARY_AGENT,
    CONF_PRIMARY_TIMEOUT,
    CONF_PROMPT_DETAILED,
    CONF_PROMPT_SHORT,
    CONF_SHORT_ANSWERS,
    DEFAULT_ANNOUNCE_MODEL,
    DEFAULT_CUSTOM_KNOWLEDGE,
    DEFAULT_ENABLE_HA_CONTEXT,
    DEFAULT_FALLBACK_AGENT,
    DEFAULT_PRIMARY_AGENT,
    DEFAULT_PRIMARY_TIMEOUT,
    DEFAULT_PROMPT_DETAILED,
    DEFAULT_PROMPT_SHORT,
    DEFAULT_SHORT_ANSWERS,
    LEGACY_PROMPTS_DETAILED,
)

_LOGGER = logging.getLogger(__name__)

RE_MARKDOWN = re.compile(r"[*#`_~]")

ERROR_PATTERNS = (
    "503",
    "service unavailable",
    "servererror",
    "high demand",
    "error talking",
    "api error",
    "rate limit",
)

UNCLEAR_MARKERS = (
    "[unverständlich]",
    "ich habe die frage leider nicht verstanden",
    "das ergibt leider keinen sinn",
)

OVERLOADED_TEXT = (
    "Die KI ist im Moment leider überlastet. "
    "Bitte versuche es in einem Moment noch einmal."
)

WEEKDAYS_DE = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")
MONTHS_DE = ("", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember")

WEATHER_TRANSLATIONS = {
    "clear-night": "klar",
    "cloudy": "bewölkt",
    "exceptional": "außergewöhnlich",
    "fog": "neblig",
    "hail": "Hagel",
    "lightning": "Gewitter",
    "lightning-rainy": "Gewitter mit Regen",
    "partlycloudy": "teilweise bewölkt",
    "pouring": "starker Regen",
    "rainy": "regnerisch",
    "snowy": "schneereich",
    "snowy-rainy": "Schneeregen",
    "sunny": "sonnig",
    "windy": "windig",
    "windy-variant": "windig",
}


@dataclass
class AnswerResult:
    """What the AI answered and how long it took."""

    text: str = ""
    """Cleaned answer without the model name."""
    speech: str = ""
    """What is spoken: the answer, plus the model name if enabled."""
    agent: str | None = None
    error: bool = False
    unclear: bool = False
    before_ai_seconds: float = 0.0
    llm_seconds: float = 0.0
    agent_seconds: dict[str, float] = field(default_factory=dict)
    timing_text: str = ""


def _fill(template: str, key: str, value: str) -> tuple[str, bool]:
    """Replace {key} or [key] in a prompt template."""
    for marker in (f"{{{key}}}", f"[{key}]"):
        if marker in template:
            return template.replace(marker, value), True
    return template, False


def is_error_reply(speech: str | None) -> bool:
    """Return True if an agent reply is empty or an error message."""
    if not speech:
        return True
    lower = speech.lower()
    return any(pattern in lower for pattern in ERROR_PATTERNS)


def is_unclear_reply(speech: str) -> bool:
    """Return True if the AI marked the question as not understood."""
    stripped = speech.strip()
    lower = stripped.lower()
    return (
        CODEWORD_UNVERSTAENDLICH in stripped
        or lower.startswith("unverständlich")
        or any(marker in lower for marker in UNCLEAR_MARKERS)
    )


class AnswerEngine:
    """Turn a question into a spoken answer using the configured agents."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the engine."""
        self.hass = hass
        self.entry = entry

    def build_prompt(
        self,
        question: str,
        device: str,
        is_followup: bool = False,
        previous_answer: str = "",
    ) -> str:
        """Build the prompt for the AI from the templates and the context."""
        opts = self.entry.options
        if is_followup:
            template = opts.get(CONF_PROMPT_DETAILED, DEFAULT_PROMPT_DETAILED)
            if template in LEGACY_PROMPTS_DETAILED:
                template = DEFAULT_PROMPT_DETAILED
            prompt, found = _fill(template, "question", question)
            if not found:
                prompt = f"{prompt.strip()}: {question}"

            prev_text = previous_answer if previous_answer else "Keine Vorabinformation"
            prompt, found = _fill(prompt, "previous_answer", prev_text)
            if not found and previous_answer:
                prompt = (
                    f"{prompt} Bereits gegebene Kurzantwort (nicht wiederholen, sondern neue Aspekte und wichtige Infos ergänzen): {previous_answer}"
                )
        elif opts.get(CONF_SHORT_ANSWERS, DEFAULT_SHORT_ANSWERS):
            template = opts.get(CONF_PROMPT_SHORT, DEFAULT_PROMPT_SHORT)
            prompt, found = _fill(template, "question", question)
            if not found:
                prompt = f"{template.strip()}: {question}"
        else:
            prompt = question

        context_str = self.ha_context_summary(device)
        if context_str:
            prompt = f"{prompt} {context_str}"
        return prompt

    async def _async_ask_agent(self, agent_id: str, prompt: str) -> str | None:
        """Ask one conversation agent and return its plain speech."""
        res = await self.hass.services.async_call(
            "conversation",
            "process",
            {"agent_id": agent_id, "text": prompt},
            blocking=True,
            return_response=True,
        )
        if res and isinstance(res, dict):
            return (
                res.get("response", {})
                .get("speech", {})
                .get("plain", {})
                .get("speech")
            )
        return None

    async def _async_timed_ask(
        self, agent_id: str, prompt: str, started: float, seconds: dict[str, float]
    ) -> str | None:
        """Ask one agent, note how long it took and return a valid reply or None."""
        try:
            speech = await self._async_ask_agent(agent_id, prompt)
        except Exception as err:  # noqa: BLE001 - any agent failure counts as no answer
            _LOGGER.warning("Agent %s failed: %s", agent_id, err)
            speech = None
        seconds[agent_id] = time.monotonic() - started
        return None if is_error_reply(speech) else speech

    async def _async_race(
        self,
        prompt: str,
        primary: str,
        fallback: str | None,
        timeout: float,
        seconds: dict[str, float],
        *,
        start_both: bool = False,
    ) -> tuple[str | None, str | None]:
        """Return the first valid reply and its agent.

        The primary agent starts alone. The fallback joins as soon as the primary
        agent fails, or after `timeout` seconds without an answer (0 = only on a
        failure), or at once with `start_both`. The slower agent is cancelled
        once one has answered.
        """
        starts: dict[str, float] = {primary: time.monotonic()}
        tasks: dict[asyncio.Task[str | None], str] = {
            asyncio.create_task(
                self._async_timed_ask(primary, prompt, starts[primary], seconds)
            ): primary
        }
        fallback_started = False

        def _start_fallback(reason: str) -> None:
            nonlocal fallback_started
            if fallback is None or fallback_started:
                return
            fallback_started = True
            _LOGGER.info("Starting fallback agent %s (%s)", fallback, reason)
            starts[fallback] = time.monotonic()
            task = asyncio.create_task(
                self._async_timed_ask(fallback, prompt, starts[fallback], seconds)
            )
            tasks[task] = fallback

        if start_both:
            _start_fallback("detailed answer, both agents race")

        try:
            while tasks:
                wait_for = timeout if timeout > 0 and not fallback_started else None
                done, _pending = await asyncio.wait(
                    tasks, timeout=wait_for, return_when=asyncio.FIRST_COMPLETED
                )
                if not done:
                    _start_fallback(f"no answer after {timeout:.1f}s")
                    continue
                for task in done:
                    agent = tasks.pop(task)
                    speech = task.result()
                    if speech:
                        return speech, agent
                    _start_fallback(f"{agent} gave no valid answer")
            return None, None
        finally:
            # The slower agent is stopped; its time so far still shows in the log
            for task, agent in tasks.items():
                task.cancel()
                seconds[agent] = time.monotonic() - starts[agent]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def async_answer(
        self,
        question: str,
        device: str,
        *,
        is_followup: bool = False,
        previous_answer: str = "",
        start_time: float | None = None,
        path: str = "",
    ) -> AnswerResult:
        """Race the primary and fallback agent and clean the winning reply."""
        if start_time is None:
            start_time = time.monotonic()
        opts = self.entry.options
        primary_agent = opts.get(CONF_PRIMARY_AGENT, DEFAULT_PRIMARY_AGENT)
        fallback_agent = opts.get(CONF_FALLBACK_AGENT, DEFAULT_FALLBACK_AGENT)

        prompt = self.build_prompt(question, device, is_followup, previous_answer)
        result = AnswerResult(agent=primary_agent)
        prompt_ready = time.monotonic()
        result.before_ai_seconds = prompt_ready - start_time

        timeout = float(opts.get(CONF_PRIMARY_TIMEOUT, DEFAULT_PRIMARY_TIMEOUT) or 0)
        use_fallback = bool(fallback_agent) and fallback_agent != primary_agent
        raw_speech, winner = await self._async_race(
            prompt,
            primary_agent,
            fallback_agent if use_fallback else None,
            timeout,
            result.agent_seconds,
            # Detailed answers are long; the faster of both agents wins
            start_both=is_followup,
        )
        is_error = raw_speech is None
        if winner:
            result.agent = winner

        result.llm_seconds = time.monotonic() - prompt_ready
        result.timing_text = " → ".join(
            f"{self.agent_display_name(agent)} {seconds:.1f}s"
            for agent, seconds in result.agent_seconds.items()
        )
        _LOGGER.info(
            "Timing (%s): before AI %.2fs, AI %.2fs [%s]",
            path,
            result.before_ai_seconds,
            result.llm_seconds,
            ", ".join(
                f"{agent} {seconds:.2f}s"
                for agent, seconds in result.agent_seconds.items()
            ),
        )

        if is_error or not raw_speech:
            result.error = True
            result.text = result.speech = OVERLOADED_TEXT
            return result

        if not is_followup and is_unclear_reply(raw_speech):
            result.unclear = True
            return result

        result.text = RE_MARKDOWN.sub("", raw_speech).strip()
        if opts.get(CONF_ANNOUNCE_MODEL, DEFAULT_ANNOUNCE_MODEL):
            agent_name = self.agent_display_name(result.agent or "")
            result.speech = f"{result.text} Beantwortet von {agent_name}."
        else:
            result.speech = result.text
        return result

    def agent_display_name(self, agent_id: str) -> str:
        """Get a human-friendly name for the conversation agent."""
        if "google" in agent_id or "gemini" in agent_id:
            return "Google Gemini"
        if "claude" in agent_id or "anthropic" in agent_id:
            return "Claude Sonnet"
        if "auto_router" in agent_id:
            return "Auto Router"
        if "owl" in agent_id:
            return "Owl Alpha"

        state = self.hass.states.get(agent_id)
        if state and state.attributes.get("friendly_name"):
            return str(state.attributes["friendly_name"])

        return "KI"

    def ha_context_summary(self, device: str) -> str:
        """Build a compact, single-line Smart Home context block for the prompt."""
        opts = self.entry.options
        if not opts.get(CONF_ENABLE_HA_CONTEXT, DEFAULT_ENABLE_HA_CONTEXT):
            return ""

        parts: list[str] = []

        # 1. Date & Time
        now = dt_util.now()
        weekday = WEEKDAYS_DE[now.weekday()]
        month_name = MONTHS_DE[now.month] if 1 <= now.month <= 12 else str(now.month)
        parts.append(
            f"Zeitpunkt: {weekday}, {now.day}. {month_name} {now.year}, {now.strftime('%H:%M')} Uhr"
        )

        # 2. Room / Location
        dev_state = self.hass.states.get(device)
        room_name = (
            dev_state.attributes.get("friendly_name")
            if dev_state and dev_state.attributes.get("friendly_name")
            else device.replace("media_player.", "").replace("_", " ").title()
        )
        parts.append(f"Standort: {room_name}")

        # 3. Weather
        weather_entity: str | None = None
        if self.hass.states.get("weather.hildesheim"):
            weather_entity = "weather.hildesheim"
        else:
            weather_states = self.hass.states.async_all("weather")
            if weather_states:
                weather_entity = weather_states[0].entity_id

        if weather_entity:
            w = self.hass.states.get(weather_entity)
            if w and w.state not in ("unavailable", "unknown"):
                cond_de = WEATHER_TRANSLATIONS.get(w.state.lower(), w.state)
                temp: Any = w.attributes.get("temperature")
                if temp is not None:
                    parts.append(f"Wetter: {cond_de}, {temp}°C")
                else:
                    parts.append(f"Wetter: {cond_de}")

        # 4. Presence (who is home)
        person_states = self.hass.states.async_all("person")
        if person_states:
            home_persons = [
                str(p.attributes.get("friendly_name") or p.entity_id.replace("person.", "").title())
                for p in person_states
                if p.state == "home" and not p.entity_id.endswith(".mcp")
            ]
            if home_persons:
                parts.append(f"Zu Hause: {', '.join(home_persons)}")

        # 5. Custom Knowledge / House Wiki
        custom_knowledge = str(
            opts.get(CONF_CUSTOM_KNOWLEDGE, DEFAULT_CUSTOM_KNOWLEDGE) or ""
        ).strip()
        if custom_knowledge:
            clean_lines = " | ".join(
                line.strip() for line in custom_knowledge.splitlines() if line.strip()
            )
            parts.append(f"Haus-Fakten: {clean_lines}")

        return f"[Smart-Home-Kontext: {' | '.join(parts)}]"
