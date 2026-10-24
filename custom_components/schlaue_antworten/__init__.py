"""The Schlaue Antworten integration."""
from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, ServiceCall, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    CODEWORD_UNVERSTAENDLICH,
    CONF_ABORT_PROMPT,
    CONF_ANNOUNCE_MODEL,
    CONF_DEFAULT_ECHO,
    CONF_DIALOG_PROMPT,
    CONF_ENABLE_DETAILED_FOLLOWUP,
    CONF_ENABLE_HA_CONTEXT,
    CONF_ENABLE_LOGGING,
    CONF_FALLBACK_AGENT,
    CONF_FOLLOWUP_PROMPT,
    CONF_GOODBYE_TEXT,
    CONF_PRIMARY_AGENT,
    CONF_PROMPT_DETAILED,
    CONF_PROMPT_SHORT,
    CONF_RETRY_PROMPT,
    CONF_SHORT_ANSWERS,
    DEFAULT_ABORT_PROMPT,
    DEFAULT_ANNOUNCE_MODEL,
    DEFAULT_DIALOG_PROMPT,
    DEFAULT_ECHO,
    DEFAULT_ENABLE_DETAILED_FOLLOWUP,
    DEFAULT_ENABLE_HA_CONTEXT,
    DEFAULT_ENABLE_LOGGING,
    DEFAULT_FALLBACK_AGENT,
    DEFAULT_FOLLOWUP_PROMPT,
    DEFAULT_GOODBYE_TEXT,
    DEFAULT_PRIMARY_AGENT,
    DEFAULT_PROMPT_DETAILED,
    DEFAULT_PROMPT_SHORT,
    DEFAULT_RETRY_PROMPT,
    DEFAULT_SHORT_ANSWERS,
    DOMAIN,
    EVENT_ACTIONABLE_NOTIFICATION,
    EVENT_ID_FOLLOWUP,
    EVENT_ID_QUERY,
    FILLER_PHRASES,
    SERVICE_ASK_QUESTION,
    SERVICE_START_DIALOG,
    TRIGGER_BOOLEAN_ENTITY,
)

_LOGGER = logging.getLogger(__name__)

RE_MARKDOWN = re.compile(r"[*#`_~]")
RE_NON_WORDS = re.compile(r"[^\w\s]")

ERROR_PATTERNS = (
    "503",
    "service unavailable",
    "servererror",
    "high demand",
    "error talking",
    "api error",
    "rate limit",
)

CANCEL_PHRASES = frozenset({
    "none",
    "responsenone",
    "responseno",
    "null",
    "undefined",
    "abbrechen",
    "stop",
    "stopp",
    "nein",
    "nichts",
})

MATH_TERMS = frozenset({
    "plus",
    "minus",
    "mal",
    "geteilt",
    "durch",
    "dividiert",
    "multipliziert",
    "wurzel",
    "summe",
    "rechen",
})

POSITIVE_PHRASES = (
    "ja",
    "gerne",
    "sicher",
    "bitte",
    "mehr",
    "ausführlich",
    "erzähl",
    "mach",
    "yes",
    "klar",
)

NEGATIVE_PHRASES = (
    "nein",
    "ne",
    "nö",
    "nicht",
    "danke",
    "stop",
    "stopp",
    "abbrechen",
    "ende",
    "schluss",
    "reicht",
    "kein",
    "keine",
    "lass",
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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Schlaue Antworten from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    manager = SchlaueAntwortenManager(hass, entry)
    await manager.async_setup()
    hass.data[DOMAIN][entry.entry_id] = manager

    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.entry_id in hass.data[DOMAIN]:
        manager: SchlaueAntwortenManager = hass.data[DOMAIN][entry.entry_id]
        await manager.async_unload()
        hass.data[DOMAIN].pop(entry.entry_id)

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options by reloading cleanly through Home Assistant's entry manager."""
    await hass.config_entries.async_reload(entry.entry_id)


class SchlaueAntwortenManager:
    """Manager class for Schlaue Antworten logic."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the manager."""
        self.hass = hass
        self.entry = entry
        self._unsub_event: Any = None
        self._unsub_state: Any = None
        self._last_questions: dict[str, Any] = {}
        self._retry_counts: dict[str, int] = {}
        self._history: list[dict[str, str]] = []

    def add_history_entry(
        self,
        device: str,
        query: str,
        output: str,
        duration: float | None = None,
        char_count: int | None = None,
        mode: str | None = None,
    ) -> None:
        """Add a compact log entry for user view in options (max 100 chars output)."""
        if not self.entry.options.get(CONF_ENABLE_LOGGING, DEFAULT_ENABLE_LOGGING):
            return

        clean_dev = device.replace("media_player.", "").replace("_", " ").title()
        now_str = dt_util.now().strftime("%H:%M")
        preview = output[:100] + ("..." if len(output) > 100 else "")

        meta_parts: list[str] = []
        if mode:
            meta_parts.append(mode)
        if char_count is not None:
            meta_parts.append(f"{char_count} Z.")
        if duration is not None:
            meta_parts.append(f"{duration:.1f}s")

        meta_str = f" ({' • '.join(meta_parts)})" if meta_parts else ""

        entry = {
            "time": now_str,
            "device": clean_dev,
            "meta": meta_str,
            "query": query,
            "output": preview,
        }
        self._history.insert(0, entry)
        if len(self._history) > 10:
            self._history = self._history[:10]

    def get_history_markdown(self) -> str:
        """Return compact markdown string of last interactions."""
        if not self.entry.options.get(CONF_ENABLE_LOGGING, DEFAULT_ENABLE_LOGGING):
            return "_Die Protokollierung (Dialog-Log) ist in den Einstellungen deaktiviert._"
        if not self._history:
            return "_Noch keine Dialoge aufgezeichnet._"
        lines = []
        for item in self._history:
            lines.append(
                f"- `{item['time']}` **{item['device']}**{item.get('meta', '')} | *In:* {item['query']} ➔ *Out:* {item['output']}"
            )
        return "\n".join(lines)

    async def async_setup(self) -> None:
        """Register listeners and services."""
        # 1. Listen for Alexa Actionable Notification responses
        self._unsub_event = self.hass.bus.async_listen(
            EVENT_ACTIONABLE_NOTIFICATION, self._async_handle_notification_event
        )

        # 2. Listen for the existing input_boolean trigger (Scene/Routine compatibility)
        self._unsub_state = async_track_state_change_event(
            self.hass,
            [TRIGGER_BOOLEAN_ENTITY],
            self._async_handle_boolean_trigger,
        )

        # 3. Register services
        self.hass.services.async_register(
            DOMAIN,
            SERVICE_START_DIALOG,
            self.async_service_start_dialog,
        )
        self.hass.services.async_register(
            DOMAIN,
            SERVICE_ASK_QUESTION,
            self.async_service_ask_question,
        )

        _LOGGER.info("Schlaue Antworten integration successfully set up")

    async def async_unload(self) -> None:
        """Unregister listeners and services."""
        if self._unsub_event:
            self._unsub_event()
            self._unsub_event = None

        if self._unsub_state:
            self._unsub_state()
            self._unsub_state = None

        self.hass.services.async_remove(DOMAIN, SERVICE_START_DIALOG)
        self.hass.services.async_remove(DOMAIN, SERVICE_ASK_QUESTION)

    def _get_target_echo(self, preferred_device: str | None = None) -> str:
        """Determine the active Echo media_player."""
        if preferred_device and self.hass.states.get(preferred_device):
            return preferred_device

        last_alexa = self.hass.states.get("sensor.last_alexa")
        if (
            last_alexa
            and last_alexa.state
            and last_alexa.state not in ("unknown", "unavailable", "")
        ):
            return last_alexa.state

        default_echo = self.entry.options.get(CONF_DEFAULT_ECHO, DEFAULT_ECHO)
        return str(default_echo)

    async def async_service_start_dialog(self, call: ServiceCall) -> None:
        """Service handler to start the dialogue on an Echo device."""
        target_device = self._get_target_echo(call.data.get("echo_device"))
        await self.async_start_dialog(target_device)

    async def async_service_ask_question(self, call: ServiceCall) -> None:
        """Service handler to directly ask a question."""
        question = call.data.get("question", "").strip()
        if not question:
            return

        target_device = self._get_target_echo(call.data.get("echo_device"))
        await self.async_process_and_speak(question, target_device)

    async def async_start_dialog(self, target_device: str) -> None:
        """Start the Actionable Notification dialog on the target Echo."""
        self._retry_counts.pop(target_device, None)
        prompt = self.entry.options.get(CONF_DIALOG_PROMPT, DEFAULT_DIALOG_PROMPT)

        # Stop active media playback only if the device is currently playing
        # This saves 1-2 seconds of cloud roundtrip latency when the device is idle
        dev_state = self.hass.states.get(target_device)
        if dev_state and dev_state.state == "playing":
            try:
                self.hass.async_create_task(
                    self.hass.services.async_call(
                        "media_player",
                        "media_stop",
                        {"entity_id": target_device},
                        blocking=False,
                    )
                )
            except Exception as err:
                _LOGGER.debug("Non-blocking media_stop ignored: %s", err)

        # Trigger actionable notification script (non-blocking for immediate execution)
        if self.hass.services.has_service(
            "script", "activate_alexa_actionable_notification"
        ):
            await self.hass.services.async_call(
                "script",
                "activate_alexa_actionable_notification",
                {
                    "text": prompt,
                    "event_id": EVENT_ID_QUERY,
                    "alexa_device": target_device,
                    "suppress_confirmation": "true",
                },
                blocking=False,
            )
        else:
            _LOGGER.warning(
                "script.activate_alexa_actionable_notification not found"
            )

    def _is_local_nonsense(self, text: str) -> bool:
        """Check if input text is obviously unclear, too short, or pure filler."""
        # Numbers, math operations, and calculations are always valid
        if any(c.isdigit() for c in text):
            return False

        cleaned = RE_NON_WORDS.sub("", text).strip().lower()
        if any(term in cleaned.split() for term in MATH_TERMS):
            return False

        if not cleaned or len(cleaned) < 3:
            return True
        words = cleaned.split()
        if len(words) == 1 and (words[0] in FILLER_PHRASES or len(words[0]) < 3):
            return True
        if cleaned in FILLER_PHRASES:
            return True
        return False

    async def _async_handle_unclear_query(
        self, reply_device: str, start_time: float | None = None
    ) -> None:
        """Handle an unclear or nonsensical question with loop protection."""
        duration = time.monotonic() - start_time if start_time else None
        current_retries = self._retry_counts.get(reply_device, 0)
        if current_retries < 1:
            self._retry_counts[reply_device] = current_retries + 1
            retry_prompt = self.entry.options.get(
                CONF_RETRY_PROMPT, DEFAULT_RETRY_PROMPT
            )
            _LOGGER.info(
                "Query unclear on %s; prompting user to repeat (retry 1)",
                reply_device,
            )
            self.add_history_entry(
                reply_device,
                "Unverständliche Spracheingabe",
                retry_prompt,
                duration=duration,
                char_count=len(retry_prompt),
                mode="Wiederholung",
            )
            if self.hass.services.has_service(
                "script", "activate_alexa_actionable_notification"
            ):
                await self.hass.services.async_call(
                    "script",
                    "activate_alexa_actionable_notification",
                    {
                        "text": retry_prompt,
                        "event_id": EVENT_ID_QUERY,
                        "alexa_device": reply_device,
                        "suppress_confirmation": "true",
                    },
                    blocking=False,
                )
            else:
                await self.hass.services.async_call(
                    "notify",
                    "alexa_media",
                    {
                        "target": [reply_device],
                        "data": {"type": "tts"},
                        "message": retry_prompt,
                    },
                    blocking=False,
                )
        else:
            self._retry_counts.pop(reply_device, None)
            abort_prompt = self.entry.options.get(
                CONF_ABORT_PROMPT, DEFAULT_ABORT_PROMPT
            )
            _LOGGER.info(
                "Query unclear again on %s; ending dialog with abort message",
                reply_device,
            )
            self.add_history_entry(
                reply_device,
                "Unverständliche Spracheingabe (Fehlversuch 2)",
                abort_prompt,
                duration=duration,
                char_count=len(abort_prompt),
                mode="Abbruch",
            )
            try:
                await self.hass.services.async_call(
                    "notify",
                    "alexa_media",
                    {
                        "target": [reply_device],
                        "data": {"type": "tts"},
                        "message": abort_prompt,
                    },
                    blocking=False,
                )
            except Exception as err:
                _LOGGER.error("Failed to speak abort prompt: %s", err)

    @callback
    def _async_handle_boolean_trigger(self, event: Event) -> None:
        """Trigger dialog when input_boolean.alexa_ki_trigger turns on."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state != "on":
            return

        # Turn boolean back off immediately and start dialog
        self.hass.async_create_task(
            self.hass.services.async_call(
                "input_boolean",
                "turn_off",
                {"entity_id": TRIGGER_BOOLEAN_ENTITY},
                blocking=False,
            )
        )
        target_device = self._get_target_echo()
        self.hass.async_create_task(self.async_start_dialog(target_device))

    async def _async_handle_notification_event(self, event: Event) -> None:
        """Process user's spoken answer from Actionable Notifications."""
        start_time = time.monotonic()
        data = event.data
        event_id = data.get("event_id")
        if event_id not in (EVENT_ID_QUERY, EVENT_ID_FOLLOWUP):
            return

        raw_response = str(data.get("event_response", "")).strip()
        resp_lower = raw_response.lower()
        response_type = str(data.get("event_response_type", "")).strip()

        # Identify reply Echo
        reply_device = str(
            data.get("entity_id")
            or data.get("device")
            or self._get_target_echo()
        )

        # Handle follow-up response (user answers yes/no to "Möchtest du mehr darüber erfahren?")
        if event_id == EVENT_ID_FOLLOWUP:
            stored_data = self._last_questions.pop(reply_device, None)
            if not stored_data:
                _LOGGER.debug(
                    "No stored question found for follow-up on %s", reply_device
                )
                return

            if isinstance(stored_data, dict):
                stored_question = str(stored_data.get("question", ""))
                previous_answer = str(stored_data.get("short_answer", ""))
            else:
                stored_question = str(stored_data)
                previous_answer = ""

            is_positive = response_type == "ResponseYes" or any(
                p in resp_lower for p in POSITIVE_PHRASES
            )

            is_negative = response_type == "ResponseNo" or any(
                p in resp_lower for p in NEGATIVE_PHRASES
            )

            if is_positive:
                _LOGGER.info(
                    "User requested detailed explanation for: %s", stored_question
                )
                await self.async_process_and_speak(
                    stored_question,
                    reply_device,
                    is_followup=True,
                    previous_answer=previous_answer,
                    start_time=start_time,
                )
            elif is_negative:
                _LOGGER.debug(
                    "User declined detailed explanation on %s: %s",
                    reply_device,
                    raw_response,
                )
                goodbye_text = self.entry.options.get(
                    CONF_GOODBYE_TEXT, DEFAULT_GOODBYE_TEXT
                )
                if goodbye_text:
                    self.add_history_entry(
                        reply_device,
                        "[Follow-up] Nein",
                        goodbye_text,
                        duration=time.monotonic() - start_time,
                        char_count=len(goodbye_text),
                        mode="Ende",
                    )
                    try:
                        await self.hass.services.async_call(
                            "notify",
                            "alexa_media",
                            {
                                "target": [reply_device],
                                "data": {"type": "tts"},
                                "message": goodbye_text,
                            },
                            blocking=False,
                        )
                    except Exception as err:
                        _LOGGER.error("Failed to speak goodbye text: %s", err)
            else:
                _LOGGER.debug(
                    "Follow-up ignored or timed out on %s (response: %s)",
                    reply_device,
                    raw_response,
                )
            return

        # Check for cancel or empty in initial query
        if not raw_response or resp_lower in CANCEL_PHRASES:
            self._retry_counts.pop(reply_device, None)
            _LOGGER.debug("Dialog cancelled or response empty: %s", raw_response)
            return

        # Check for local nonsense, filler words, or too short input
        if self._is_local_nonsense(raw_response):
            await self._async_handle_unclear_query(
                reply_device, start_time=start_time
            )
            return

        await self.async_process_and_speak(
            raw_response, reply_device, is_followup=False, start_time=start_time
        )

    async def async_process_and_speak(
        self,
        question: str,
        reply_device: str,
        is_followup: bool = False,
        previous_answer: str = "",
        start_time: float | None = None,
    ) -> None:
        """Query LLM and output answer via Alexa."""
        if start_time is None:
            start_time = time.monotonic()

        opts = self.entry.options
        primary_agent = opts.get(CONF_PRIMARY_AGENT, DEFAULT_PRIMARY_AGENT)
        fallback_agent = opts.get(CONF_FALLBACK_AGENT, DEFAULT_FALLBACK_AGENT)
        short_answers = opts.get(CONF_SHORT_ANSWERS, DEFAULT_SHORT_ANSWERS)
        announce_model = opts.get(CONF_ANNOUNCE_MODEL, DEFAULT_ANNOUNCE_MODEL)
        enable_followup = opts.get(
            CONF_ENABLE_DETAILED_FOLLOWUP, DEFAULT_ENABLE_DETAILED_FOLLOWUP
        )
        followup_prompt = opts.get(
            CONF_FOLLOWUP_PROMPT, DEFAULT_FOLLOWUP_PROMPT
        )
        prompt_short_tmpl = opts.get(CONF_PROMPT_SHORT, DEFAULT_PROMPT_SHORT)
        prompt_detailed_tmpl = opts.get(
            CONF_PROMPT_DETAILED, DEFAULT_PROMPT_DETAILED
        )

        if is_followup:
            prompt = prompt_detailed_tmpl
            if "{question}" in prompt:
                prompt = prompt.replace("{question}", question)
            elif "[question]" in prompt:
                prompt = prompt.replace("[question]", question)
            else:
                prompt = f"{prompt.strip()}: {question}"

            prev_text = previous_answer if previous_answer else "Keine Vorabinformation"
            if "{previous_answer}" in prompt:
                prompt = prompt.replace("{previous_answer}", prev_text)
            elif "[previous_answer]" in prompt:
                prompt = prompt.replace("[previous_answer]", prev_text)
            elif previous_answer:
                prompt = (
                    f"{prompt} Bereits gegebene Kurzantwort (nicht wiederholen, sondern neue Aspekte und wichtige Infos ergänzen): {previous_answer}"
                )
        elif short_answers:
            if "{question}" in prompt_short_tmpl:
                prompt = prompt_short_tmpl.replace("{question}", question)
            elif "[question]" in prompt_short_tmpl:
                prompt = prompt_short_tmpl.replace("[question]", question)
            else:
                prompt = f"{prompt_short_tmpl.strip()}: {question}"
        else:
            prompt = question

        # Append compact Smart Home context (weather, time, location, presence) if enabled
        context_str = self._get_ha_context_summary(reply_device)
        if context_str:
            prompt = f"{prompt} {context_str}"

        raw_speech: str | None = None
        used_agent: str = primary_agent

        # 1. Try primary agent
        try:
            res = await self.hass.services.async_call(
                "conversation",
                "process",
                {"agent_id": primary_agent, "text": prompt},
                blocking=True,
                return_response=True,
            )
            if res and isinstance(res, dict):
                raw_speech = (
                    res.get("response", {})
                    .get("speech", {})
                    .get("plain", {})
                    .get("speech")
                )
        except Exception as err:
            _LOGGER.warning("Primary agent %s failed: %s", primary_agent, err)

        # 2. Check if primary agent output is an error or empty
        is_error = False
        if not raw_speech:
            is_error = True
        else:
            speech_lower = raw_speech.lower()
            if any(pattern in speech_lower for pattern in ERROR_PATTERNS):
                is_error = True

        # 3. Fallback agent if needed
        if is_error and fallback_agent and fallback_agent != primary_agent:
            _LOGGER.info(
                "Primary agent returned error; invoking fallback agent %s",
                fallback_agent,
            )
            try:
                res_fb = await self.hass.services.async_call(
                    "conversation",
                    "process",
                    {"agent_id": fallback_agent, "text": prompt},
                    blocking=True,
                    return_response=True,
                )
                if res_fb and isinstance(res_fb, dict):
                    fb_speech = (
                        res_fb.get("response", {})
                        .get("speech", {})
                        .get("plain", {})
                        .get("speech")
                    )
                    if fb_speech and not any(
                        p in fb_speech.lower() for p in ERROR_PATTERNS
                    ):
                        raw_speech = fb_speech
                        used_agent = fallback_agent
                        is_error = False
            except Exception as err:
                _LOGGER.error("Fallback agent %s also failed: %s", fallback_agent, err)

        # 4. Error response
        if is_error or not raw_speech:
            final_speech = (
                "Die KI ist im Moment leider überlastet. "
                "Bitte versuche es in einem Moment noch einmal."
            )
            duration = time.monotonic() - start_time
            self.add_history_entry(
                reply_device,
                question,
                final_speech,
                duration=duration,
                char_count=len(final_speech),
                mode="Fehler",
            )
            try:
                await self.hass.services.async_call(
                    "notify",
                    "alexa_media",
                    {
                        "target": [reply_device],
                        "data": {"type": "tts"},
                        "message": final_speech,
                    },
                    blocking=False,
                )
            except Exception as err:
                _LOGGER.error("Failed to speak error via notify.alexa_media: %s", err)
            return

        # 5. Check if AI deemed the query unclear or nonsensical
        speech_stripped = raw_speech.strip()
        speech_lower = speech_stripped.lower()
        if not is_followup and (
            CODEWORD_UNVERSTAENDLICH in speech_stripped
            or speech_lower.startswith("unverständlich")
            or "[unverständlich]" in speech_lower
            or "ich habe die frage leider nicht verstanden" in speech_lower
            or "das ergibt leider keinen sinn" in speech_lower
        ):
            await self._async_handle_unclear_query(
                reply_device, start_time=start_time
            )
            return

        # Query was successful and understood -> clear retry counter
        self._retry_counts.pop(reply_device, None)

        # 6. Clean markdown formatting (*, #, `, _, ~)
        cleaned = RE_MARKDOWN.sub("", raw_speech).strip()
        if announce_model:
            agent_name = self._get_agent_display_name(used_agent)
            final_speech = f"{cleaned} Beantwortet von {agent_name}."
        else:
            final_speech = cleaned

        # Log interaction (with latency and character count)
        duration = time.monotonic() - start_time
        mode_label = "Lang" if is_followup else "Kurz"
        self.add_history_entry(
            device=reply_device,
            query=f"[Vertiefung] {question}" if is_followup else question,
            output=final_speech,
            duration=duration,
            char_count=len(final_speech),
            mode=mode_label,
        )

        # 7. Actionable Notification with follow-up question if enabled
        if not is_followup and enable_followup:
            self._last_questions[reply_device] = {
                "question": question,
                "short_answer": cleaned,
            }
            combined_message = f"{final_speech} {followup_prompt}"

            if self.hass.services.has_service(
                "script", "activate_alexa_actionable_notification"
            ):
                # If message is compact (<= 170 chars), Alexa can speak answer + followup in one notification
                if len(combined_message) <= 170:
                    await self.hass.services.async_call(
                        "script",
                        "activate_alexa_actionable_notification",
                        {
                            "text": combined_message,
                            "event_id": EVENT_ID_FOLLOWUP,
                            "alexa_device": reply_device,
                            "suppress_confirmation": "true",
                        },
                        blocking=False,
                    )
                    return

                # For longer answers: play short answer via TTS first to avoid 255-char input_text limit,
                # then ask the follow-up prompt with open microphone
                try:
                    await self.hass.services.async_call(
                        "notify",
                        "alexa_media",
                        {
                            "target": [reply_device],
                            "data": {"type": "tts"},
                            "message": final_speech,
                        },
                        blocking=False,
                    )
                except Exception as err:
                    _LOGGER.warning("TTS error on %s: %s", reply_device, err)

                # Wait for TTS to finish (approx 13 chars per second + 0.5s pause)
                wait_duration = max(2.5, (len(final_speech) / 13.0) + 0.5)
                await asyncio.sleep(wait_duration)

                # Now trigger the follow-up question with open microphone
                await self.hass.services.async_call(
                    "script",
                    "activate_alexa_actionable_notification",
                    {
                        "text": followup_prompt,
                        "event_id": EVENT_ID_FOLLOWUP,
                        "alexa_device": reply_device,
                        "suppress_confirmation": "true",
                    },
                    blocking=False,
                )
                return

        # 8. Standard TTS output
        try:
            await self.hass.services.async_call(
                "notify",
                "alexa_media",
                {
                    "target": [reply_device],
                    "data": {"type": "tts"},
                    "message": final_speech,
                },
                blocking=False,
            )
        except Exception as err:
            _LOGGER.error("Failed to speak via notify.alexa_media: %s", err)

    def _get_agent_display_name(self, agent_id: str) -> str:
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

    def _get_ha_context_summary(self, reply_device: str) -> str:
        """Build a compact, single-line Smart Home context block for the LLM prompt."""
        if not self.entry.options.get(
            CONF_ENABLE_HA_CONTEXT, DEFAULT_ENABLE_HA_CONTEXT
        ):
            return ""

        parts: list[str] = []

        # 1. Date & Time
        now = dt_util.now()
        weekday = WEEKDAYS_DE[now.weekday()]
        month_name = (
            MONTHS_DE[now.month] if 1 <= now.month <= 12 else str(now.month)
        )
        parts.append(
            f"Zeitpunkt: {weekday}, {now.day}. {month_name} {now.year}, {now.strftime('%H:%M')} Uhr"
        )

        # 2. Room / Location
        dev_state = self.hass.states.get(reply_device)
        room_name = (
            dev_state.attributes.get("friendly_name")
            if dev_state and dev_state.attributes.get("friendly_name")
            else reply_device.replace("media_player.", "").replace("_", " ").title()
        )
        parts.append(f"Standort: {room_name}")

        # 3. Weather
        weather_entity = None
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
                temp = w.attributes.get("temperature")
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

        return f"[Smart-Home-Kontext: {' | '.join(parts)}]"

