"""Connection between the user's own Alexa skill and Schlaue Antworten.

The skill (Alexa-hosted, code from skill_model.py) posts each request to a
secret webhook. The answer goes straight back in the HTTP reply,
so Alexa speaks it at once, without a second trip through Alexa Media.
"""
from __future__ import annotations

import asyncio
from collections import deque
import json
import logging
import secrets
import time
from typing import TYPE_CHECKING, Any

from aiohttp import hdrs, web

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.network import get_url
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .answer import AnswerResult
from .claude_bridge import SendResult
from .const import (
    CLAUDE_BUSY_TEXT,
    CLAUDE_EMPTY_TEXT,
    CLAUDE_NOT_ALLOWED_TEXT,
    CLAUDE_NOT_SET_UP_TEXT,
    CLAUDE_OFF_TEXT,
    CLAUDE_SENT_TEXT,
    CLAUDE_UNKNOWN_ECHO_TEXT,
    CLAUDE_UNREACHABLE_TEXT,
    CONF_DEFAULT_ECHO,
    CONF_ABORT_PROMPT,
    CONF_DIALOG_PROMPT,
    CONF_ENABLE_DETAILED_FOLLOWUP,
    CONF_FOLLOWUP_PROMPT,
    CONF_GOODBYE_TEXT,
    CONF_INVOCATION_NAME,
    CONF_LATE_TEXT,
    CONF_MOBILE_CONFIRMATION,
    CONF_RETRY_PROMPT,
    CONF_SKILL_KEEP_OPEN,
    DEFAULT_ABORT_PROMPT,
    DEFAULT_DIALOG_PROMPT,
    DEFAULT_ENABLE_DETAILED_FOLLOWUP,
    DEFAULT_FOLLOWUP_PROMPT,
    DEFAULT_ECHO,
    DEFAULT_GOODBYE_TEXT,
    DEFAULT_INVOCATION_NAME,
    DEFAULT_LATE_TEXT,
    DEFAULT_MOBILE_CONFIRMATION,
    DEFAULT_RETRY_PROMPT,
    DEFAULT_SKILL_KEEP_OPEN,
    DOMAIN,
    MOBILE_QUESTION_PHRASES,
    SKILL_ANOTHER_TEXT,
    SKILL_ASK_TEXT,
    SKILL_HELP_TEXT,
    SKILL_PHONE_NOTHING_TEXT,
    SKILL_ROOM_NO_DEVICE_TEXT,
    SKILL_ROOM_SET_TEXT,
    SKILL_ROOM_UNKNOWN_TEXT,
)
from .echo_match import best_echo, echo_candidates
from .skill_model import (
    INTENT_CLAUDE,
    INTENT_PHONE,
    INTENT_ROOM,
    INTENT_START,
    build_skill_code,
    interaction_model_json,
    question_from_intent,
)

if TYPE_CHECKING:
    from . import SchlaueAntwortenManager

_LOGGER = logging.getLogger(__name__)

SKILL_STORAGE_KEY = f"{DOMAIN}_skill"
SKILL_STORAGE_VERSION = 1

PATH_SKILL = "skill"

ACTION_ASK = "ask"
ACTION_LAUNCH = "launch"
ACTION_INTENT = "intent"
ACTIONS = (ACTION_ASK, ACTION_LAUNCH, ACTION_INTENT)
MAX_INTENT_LENGTH = 100
# Session attributes the skill keeps between turns of one dialog
SESSION_STAGE = "stage"
SESSION_QUESTION = "question"
SESSION_ANSWER = "answer"
STAGE_FOLLOWUP = "followup"
SESSION_RETRIES = "retries"
SESSION_DETAIL = "detail"
# A detailed answer computed ahead of "Ja" is kept this long
PREFETCH_SECONDS = 120.0
# How long "schick es aufs Handy" still finds the last answer of an Echo
LAST_ANSWER_SECONDS = 15 * 60.0

INTENTS_GOODBYE = ("AMAZON.StopIntent", "AMAZON.CancelIntent", "AMAZON.NoIntent")
INTENTS_SILENT_OK = ("AMAZON.NavigateHomeIntent",)

MAX_TEXT_LENGTH = 500
MAX_SPEECH_LENGTH = 7900
# The skill code gives Home Assistant 6.5 seconds, Amazon waits about 8
SKILL_BUDGET_SECONDS = 6.0
SAVE_DELAY_SECONDS = 30.0
MAX_SEEN_DEVICES = 20
RATE_LIMIT_REQUESTS = 20
RATE_LIMIT_WINDOW_SECONDS = 60.0

CLAUDE_TEXTS: dict[SendResult, str] = {
    SendResult.SENT: CLAUDE_SENT_TEXT,
    SendResult.OFF: CLAUDE_OFF_TEXT,
    SendResult.NOT_SET_UP: CLAUDE_NOT_SET_UP_TEXT,
    SendResult.NOT_ALLOWED: CLAUDE_NOT_ALLOWED_TEXT,
    SendResult.BUSY: CLAUDE_BUSY_TEXT,
    SendResult.UNREACHABLE: CLAUDE_UNREACHABLE_TEXT,
}


class SkillConnector:
    """Serve the webhook that the own Alexa skill calls."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        manager: SchlaueAntwortenManager,
    ) -> None:
        """Initialize the connector."""
        self.hass = hass
        self.entry = entry
        self.manager = manager
        self._store: Store[dict[str, Any]] = Store(
            hass, SKILL_STORAGE_VERSION, SKILL_STORAGE_KEY
        )
        self._webhook_id = ""
        self._application_id: str | None = None
        self._devices: dict[str, str] = {}
        # Alexa device id -> when it last asked, to assign it in the options
        self._seen: dict[str, str] = {}
        self._requests: deque[float] = deque()
        self._active = False
        self.last_request: dict[str, str] | None = None
        self.last_skill_request: dict[str, str] | None = None
        self._prefetched: dict[str, tuple[asyncio.Task[AnswerResult], float]] = {}
        # Echo -> (question, answer, time) for "schick es aufs Handy"
        self._last_answers: dict[str, tuple[str, str, float]] = {}

    @property
    def is_linked(self) -> bool:
        """Return whether a skill has been linked to this installation."""
        return self._application_id is not None

    @property
    def is_active(self) -> bool:
        """Return whether the webhook currently accepts requests."""
        return self._active

    @property
    def webhook_id(self) -> str:
        """Return the secret webhook id."""
        return self._webhook_id

    async def async_load(self) -> None:
        """Load the stored secret, skill link and known Echos."""
        data = await self._store.async_load() or {}
        self._webhook_id = str(data.get("webhook_id") or "")
        application_id = data.get("application_id")
        self._application_id = str(application_id) if application_id else None
        devices = data.get("devices")
        self._devices = dict(devices) if isinstance(devices, dict) else {}
        seen = data.get("seen")
        self._seen = dict(seen) if isinstance(seen, dict) else {}
        if not self._webhook_id:
            await self._async_new_webhook_id()

    async def _async_save(self) -> None:
        """Persist the secret, skill link and known Echos."""
        await self._store.async_save(self._data())

    @callback
    def _data(self) -> dict[str, Any]:
        """Return what is stored."""
        return {
            "webhook_id": self._webhook_id,
            "application_id": self._application_id,
            "devices": self._devices,
            "seen": self._seen,
        }

    async def _async_new_webhook_id(self) -> None:
        """Create a new secret, which invalidates the old skill code."""
        self._webhook_id = f"{DOMAIN}_{secrets.token_hex(24)}"
        self._application_id = None
        self._devices = {}
        self._seen = {}
        await self._async_save()

    @callback
    def async_start(self) -> None:
        """Start accepting requests from the skill."""
        if self._active:
            return
        webhook.async_register(
            self.hass,
            DOMAIN,
            "Schlaue Antworten Alexa Skill",
            self._webhook_id,
            self._async_handle_webhook,
            local_only=False,
            allowed_methods=[hdrs.METH_POST],
        )
        self._active = True

    @callback
    def async_stop(self) -> None:
        """Stop accepting requests from the skill."""
        if self._active:
            webhook.async_unregister(self.hass, self._webhook_id)
            self._active = False
        for task, _started in self._prefetched.values():
            task.cancel()
        self._prefetched.clear()

    def _prefetch_detail(self, question: str, answer: str, device: str) -> str:
        """Start the detailed answer while Alexa still asks "Ja oder Nein?".

        Returns the id the skill keeps in its session to collect it on "Ja".
        """
        self._drop_prefetched(older_than=PREFETCH_SECONDS)
        detail_id = secrets.token_hex(8)
        task = self.hass.async_create_task(
            self.manager.answers.async_answer(
                question,
                device,
                is_followup=True,
                previous_answer=answer,
                start_time=time.monotonic(),
                path=PATH_SKILL,
            )
        )
        self.manager.track_task(task)
        self._prefetched[detail_id] = (task, time.monotonic())
        return detail_id

    def _drop_prefetched(self, older_than: float = 0.0) -> None:
        """Cancel detailed answers nobody asked for."""
        now = time.monotonic()
        for detail_id, (task, started) in list(self._prefetched.items()):
            if now - started >= older_than:
                task.cancel()
                del self._prefetched[detail_id]

    def _take_prefetched(
        self, session: dict[str, Any]
    ) -> asyncio.Task[AnswerResult] | None:
        """Return the detailed answer started for this dialog, if still running."""
        detail_id = session.get(SESSION_DETAIL)
        if not isinstance(detail_id, str) or detail_id not in self._prefetched:
            return None
        task, _started = self._prefetched.pop(detail_id)
        if task.cancelled():
            return None
        return task

    async def async_reset(self) -> None:
        """Replace the secret and remove the skill link."""
        was_active = self._active
        self.async_stop()
        await self._async_new_webhook_id()
        if was_active:
            self.async_start()
        _LOGGER.info("Skill link reset; the skill code must be copied again")

    def webhook_url(self) -> str:
        """Return the public address the skill must call.

        Raises NoURLAvailableError if Home Assistant has no public HTTPS address.
        """
        # webhook.async_generate_url() leaves out Home Assistant Cloud addresses
        base_url = get_url(
            self.hass, allow_internal=False, allow_ip=False, require_ssl=True
        )
        return f"{base_url}{webhook.async_generate_path(self._webhook_id)}"

    def get_skill_code(self) -> str:
        """Return the skill code with the secret address filled in.

        Raises NoURLAvailableError if Home Assistant has no public HTTPS address.
        """
        return build_skill_code(self.webhook_url())

    def get_interaction_model(self) -> str:
        """Return the voice model for the Alexa developer console."""
        invocation = self.entry.options.get(
            CONF_INVOCATION_NAME, DEFAULT_INVOCATION_NAME
        )
        return interaction_model_json(str(invocation or DEFAULT_INVOCATION_NAME))

    def _rate_limited(self) -> bool:
        """Return True if too many requests arrived within the last minute."""
        now = time.monotonic()
        while self._requests and now - self._requests[0] > RATE_LIMIT_WINDOW_SECONDS:
            self._requests.popleft()
        if len(self._requests) >= RATE_LIMIT_REQUESTS:
            return True
        self._requests.append(now)
        return False

    @property
    def seen_devices(self) -> dict[str, str]:
        """Return Alexa device id -> when it last asked, newest first."""
        return dict(sorted(self._seen.items(), key=lambda item: item[1], reverse=True))

    @property
    def device_map(self) -> dict[str, str]:
        """Return Alexa device id -> Echo entity."""
        return dict(self._devices)

    async def async_set_device_map(self, device_map: dict[str, str]) -> None:
        """Replace the Echo assignment, as corrected in the options."""
        self._devices = {
            device_id: entity_id
            for device_id, entity_id in device_map.items()
            if device_id in self._seen and entity_id
        }
        await self._async_save()

    @callback
    def _note_device(self, device_id: str | None) -> None:
        """Remember that a device asked, without slowing the answer down."""
        if not device_id:
            return
        # Sortable, and readable in the options
        self._seen[device_id] = dt_util.now().strftime("%Y-%m-%d %H:%M")
        while len(self._seen) > MAX_SEEN_DEVICES:
            oldest = min(self._seen, key=self._seen.__getitem__)
            self._seen.pop(oldest)
            self._devices.pop(oldest, None)
        self._store.async_delay_save(self._data, SAVE_DELAY_SECONDS)

    async def _async_assign_room(
        self, device_id: str | None, spoken: str
    ) -> web.Response:
        """Assign this Echo by the room the user names."""
        if not device_id:
            return self._speech(SKILL_ROOM_NO_DEVICE_TEXT)
        echo = best_echo(spoken, echo_candidates(self.hass))
        if echo is None:
            return self._speech(SKILL_ROOM_UNKNOWN_TEXT.format(room=spoken.strip()))
        self._devices[device_id] = echo
        await self._async_save()
        state = self.hass.states.get(echo)
        name = str(state.attributes.get("friendly_name") or echo) if state else echo
        _LOGGER.info("Assigned an Alexa device to %s", echo)
        return self._speech(SKILL_ROOM_SET_TEXT.format(echo=name))

    def _echo_for(self, device_id: str | None) -> str:
        """Return the Echo entity for an Alexa device id, or the default Echo."""
        if device_id and device_id in self._devices:
            return self._devices[device_id]
        return str(self.entry.options.get(CONF_DEFAULT_ECHO, DEFAULT_ECHO))

    @staticmethod
    def _speech(
        text: str,
        end_session: bool = True,
        reprompt: str | None = None,
        session: dict[str, Any] | None = None,
    ) -> web.Response:
        """Return the reply the skill code turns into Alexa speech."""
        reply: dict[str, Any] = {
            "speech": text[:MAX_SPEECH_LENGTH],
            "end_session": end_session,
        }
        if reprompt and not end_session:
            reply["reprompt"] = reprompt[:MAX_SPEECH_LENGTH]
        if session:
            reply["session"] = session
        return web.json_response(reply)

    def _ask_again(self, text: str) -> web.Response:
        """Say a text and keep the microphone open for the next question."""
        return self._speech(text, end_session=False, reprompt=text)

    async def _async_handle_webhook(
        self, hass: HomeAssistant, webhook_id: str, request: web.Request
    ) -> web.Response:
        """Handle a request from the skill."""
        start_time = time.monotonic()
        try:
            payload = await request.json()
        except ValueError:
            return web.Response(status=400)
        if not isinstance(payload, dict):
            return web.Response(status=400)

        application_id = payload.get("application_id")
        action = payload.get("action", ACTION_ASK)
        text = payload.get("text") or ""
        device_id = payload.get("device_id")
        intent = payload.get("intent")
        session = payload.get("session") or {}
        if (
            not isinstance(application_id, str)
            or not application_id
            or action not in ACTIONS
            or not isinstance(text, str)
            or not isinstance(device_id, str | None)
            or not isinstance(intent, str | None)
            or (intent is not None and len(intent) > MAX_INTENT_LENGTH)
            or not isinstance(session, dict)
        ):
            return web.Response(status=400)

        # The first skill to call the secret address becomes the linked one
        if self._application_id is None:
            self._application_id = application_id
            await self._async_save()
            _LOGGER.info("Linked the own Alexa skill")
        elif application_id != self._application_id:
            _LOGGER.warning("Rejected a request from an unknown Alexa skill")
            return web.Response(status=403)

        if self._rate_limited():
            _LOGGER.warning("Too many skill requests, slowing down")
            return web.Response(status=429)

        self._note_device(device_id)
        response = await self._async_dispatch(
            action, intent, text, device_id, session, start_time
        )
        self._remember(action, intent, text, response)
        return response

    def _remember(
        self, action: str, intent: str | None, text: str, response: web.Response
    ) -> None:
        """Keep the latest skill request for the sensor, to see what Alexa sent."""
        try:
            reply = json.loads(response.text or "{}")
        except ValueError:
            reply = {}
        self.last_skill_request = {
            "zeit": dt_util.now().strftime("%d.%m. %H:%M:%S"),
            "intent": intent or action,
            "text": text[:MAX_TEXT_LENGTH],
            "antwort": str(reply.get("speech", ""))[:200],
            "offen": str(not reply.get("end_session", True)),
        }
        self.manager.notify_stats_listeners()

    async def _async_dispatch(
        self,
        action: str,
        intent: str | None,
        text: str,
        device_id: str | None,
        session: dict[str, Any],
        start_time: float,
    ) -> web.Response:
        """Answer a valid request from the linked skill."""
        retries = session.get(SESSION_RETRIES)
        retries = retries if isinstance(retries, int) else 0
        if action == ACTION_LAUNCH or intent == INTENT_START:
            return self._ask_again(
                self._option(CONF_DIALOG_PROMPT, DEFAULT_DIALOG_PROMPT)
            )

        if action == ACTION_INTENT:
            if intent == "AMAZON.YesIntent" and (
                followup := self._followup_from(session)
            ):
                return await self._async_ask(
                    followup[0],
                    self._echo_for(device_id),
                    start_time,
                    previous_answer=followup[1],
                    answer_task=self._take_prefetched(session),
                )
            if intent == INTENT_ROOM:
                return await self._async_assign_room(device_id, text)
            if intent == INTENT_CLAUDE:
                return await self._async_to_claude(device_id, text)
            if intent == INTENT_PHONE:
                return await self._async_send_to_phone(
                    self._echo_for(device_id), session
                )
            question = question_from_intent(intent, text)
            if question is None:
                return self._answer_other_intent(intent, session, retries)
        else:
            question = text

        question = " ".join(question.split())[:MAX_TEXT_LENGTH]
        if len(question) < 2:
            return self._not_understood(retries)

        return await self._async_ask(
            question, self._echo_for(device_id), start_time, retries=retries
        )

    async def _async_to_claude(
        self, device_id: str | None, text: str
    ) -> web.Response:
        """Hand a spoken prompt to the Claude session.

        Only an Echo assigned to this exact Alexa device may send, never the
        default Echo, so an unknown device cannot reach Claude.
        """
        prompt = " ".join(text.split())
        if len(prompt) < 2:
            return self._ask_again(CLAUDE_EMPTY_TEXT)
        echo = self._devices.get(device_id) if device_id else None
        if echo is None and self.manager.claude.is_set_up:
            return self._speech(CLAUDE_UNKNOWN_ECHO_TEXT)
        result = await self.manager.claude.async_send(prompt, echo)
        return self._speech(CLAUDE_TEXTS[result])

    def _not_understood(self, retries: int) -> web.Response:
        """Ask once more to repeat, the second time end the dialog.

        Without this, every sentence in an open dialog that Alexa cannot match
        leads to the fallback again, and the dialog never ends.
        """
        if retries >= 1:
            return self._speech(self._option(CONF_ABORT_PROMPT, DEFAULT_ABORT_PROMPT))
        text = self._retry_prompt()
        return self._speech(
            text, end_session=False, reprompt=text, session={SESSION_RETRIES: 1}
        )

    @staticmethod
    def _followup_from(session: dict[str, Any]) -> tuple[str, str] | None:
        """Return question and short answer if Alexa just offered more detail."""
        question = session.get(SESSION_QUESTION)
        answer = session.get(SESSION_ANSWER)
        if (
            session.get(SESSION_STAGE) != STAGE_FOLLOWUP
            or not isinstance(question, str)
            or not isinstance(answer, str)
            or not question.strip()
        ):
            return None
        return question[:MAX_TEXT_LENGTH], answer[:MAX_SPEECH_LENGTH]

    @property
    def offers_detail(self) -> bool:
        """Return whether a short answer is followed by the offer of more detail."""
        return bool(
            self.entry.options.get(
                CONF_ENABLE_DETAILED_FOLLOWUP, DEFAULT_ENABLE_DETAILED_FOLLOWUP
            )
        )

    def _answer_other_intent(
        self, intent: str | None, session: dict[str, Any], retries: int
    ) -> web.Response:
        """Answer intents that are not a question."""
        if (detail := self._take_prefetched(session)) is not None:
            # "Nein", "Stopp" or anything else: the detailed answer is not needed
            detail.cancel()
        if (
            intent == "AMAZON.NoIntent"
            and self.keeps_dialog_open
            and self._followup_from(session)
        ):
            # "Nein" to more detail, but the dialog goes on
            return self._ask_again(SKILL_ANOTHER_TEXT)
        if intent in INTENTS_GOODBYE:
            return self._speech(self._option(CONF_GOODBYE_TEXT, DEFAULT_GOODBYE_TEXT))
        if intent == "AMAZON.HelpIntent":
            return self._ask_again(SKILL_HELP_TEXT)
        if intent == "AMAZON.YesIntent":
            # "Ja" to "Noch eine Frage?"
            return self._ask_again(SKILL_ASK_TEXT)
        if intent in INTENTS_SILENT_OK:
            return self._speech("Okay.")
        # AMAZON.FallbackIntent and anything unknown
        return self._not_understood(retries)

    @property
    def keeps_dialog_open(self) -> bool:
        """Return whether the microphone stays open after an answer."""
        return bool(
            self.entry.options.get(CONF_SKILL_KEEP_OPEN, DEFAULT_SKILL_KEEP_OPEN)
        )

    def _answer(self, text: str) -> web.Response:
        """Say an answer and, if wanted, offer the next question."""
        if not self.keeps_dialog_open:
            return self._speech(text)
        return self._speech(
            f"{text} {SKILL_ANOTHER_TEXT}",
            end_session=False,
            reprompt=SKILL_ANOTHER_TEXT,
        )

    def _retry_prompt(self) -> str:
        """Return the text that asks to repeat the question."""
        return self._option(CONF_RETRY_PROMPT, DEFAULT_RETRY_PROMPT)

    def _option(self, key: str, default: str) -> str:
        """Return a text option, falling back to its default when empty."""
        return str(self.entry.options.get(key, default) or default)

    def _mobile_confirmation(self) -> str:
        """Return the sentence that confirms the push to the smartphone."""
        return self._option(CONF_MOBILE_CONFIRMATION, DEFAULT_MOBILE_CONFIRMATION)

    async def _async_push(self, question: str, answer: str, device: str) -> None:
        """Send an answer to the smartphone and note it in the history."""
        await self.manager.async_send_to_mobile(
            question=question, answer=answer, reply_device=device, confirm=False
        )
        self.manager.add_history_entry(
            device,
            f"[Smartphone] {question}",
            self._mobile_confirmation(),
            char_count=len(answer),
            mode="Push",
            timing=PATH_SKILL,
        )

    async def _async_send_to_phone(
        self, device: str, session: dict[str, Any]
    ) -> web.Response:
        """Send the last answer to the smartphone.

        In the dialog the answer comes from the session. After the dialog has
        ended, the last answer of this Echo is used for a while.
        """
        detail = self._take_prefetched(session)
        question_answer: tuple[str, str] | None = self._followup_from(session)
        if question_answer and detail is not None and detail.done():
            # The detailed answer is ready already: send it instead
            if not detail.cancelled() and detail.exception() is None:
                result = detail.result()
                if not result.error and not result.unclear and result.text:
                    question_answer = (question_answer[0], result.text)
        if detail is not None:
            detail.cancel()
        if question_answer is None:
            last = self._last_answers.get(device)
            if last and time.monotonic() - last[2] <= LAST_ANSWER_SECONDS:
                question_answer = (last[0], last[1])
        if question_answer is None:
            return self._speech(SKILL_PHONE_NOTHING_TEXT)
        await self._async_push(question_answer[0], question_answer[1], device)
        return self._answer(self._mobile_confirmation())

    async def _async_ask(
        self,
        question: str,
        device: str,
        start_time: float,
        *,
        previous_answer: str | None = None,
        retries: int = 0,
        answer_task: asyncio.Task[AnswerResult] | None = None,
    ) -> web.Response:
        """Answer a question within the skill's time limit.

        With a previous answer, the user said "Ja" to the offer of more detail.
        """
        is_followup = previous_answer is not None
        manager = self.manager
        self.last_request = {
            "time": dt_util.now().strftime("%d.%m. %H:%M:%S"),
            "text": question,
        }
        result = await manager.async_answer_within_budget(
            question,
            device,
            is_followup=is_followup,
            previous_answer=previous_answer or "",
            start_time=start_time,
            path=PATH_SKILL,
            budget=SKILL_BUDGET_SECONDS,
            answer_task=answer_task,
        )
        if result is None:
            return self._speech(self._option(CONF_LATE_TEXT, DEFAULT_LATE_TEXT))

        duration = time.monotonic() - start_time
        if result.error:
            manager.add_history_entry(
                device,
                question,
                result.speech,
                duration=duration,
                char_count=len(result.speech),
                mode="Fehler",
                timing=f"{result.timing_text} • {PATH_SKILL}",
            )
            return self._speech(result.speech)

        if result.unclear:
            return self._not_understood(retries)

        manager.add_history_entry(
            device,
            f"[Vertiefung] {question}" if is_followup else question,
            result.speech,
            duration=duration,
            char_count=len(result.speech),
            mode="Lang" if is_followup else "Kurz",
            timing=f"KI {result.timing_text} • {PATH_SKILL}",
        )
        manager.record_query_stats(
            device=device,
            query=question,
            is_followup=is_followup,
            duration=duration,
            llm_seconds=result.llm_seconds,
            agent=result.agent,
            path=PATH_SKILL,
        )
        self._last_answers[device] = (question, result.text, time.monotonic())
        if not is_followup and any(
            phrase in question.lower() for phrase in MOBILE_QUESTION_PHRASES
        ):
            # "... und schick es mir aufs Handy": answer and send, no offer of more
            await self._async_push(question, result.text, device)
            return self._answer(f"{result.speech} {self._mobile_confirmation()}")
        if is_followup or not self.offers_detail:
            return self._answer(result.speech)
        prompt = self._option(CONF_FOLLOWUP_PROMPT, DEFAULT_FOLLOWUP_PROMPT)
        return self._speech(
            f"{result.speech} {prompt}",
            end_session=False,
            reprompt=prompt,
            session={
                SESSION_STAGE: STAGE_FOLLOWUP,
                SESSION_QUESTION: question,
                SESSION_ANSWER: result.speech,
                SESSION_DETAIL: self._prefetch_detail(question, result.speech, device),
            },
        )
