"""Connection between the user's own Alexa skill and Schlaue Antworten.

The skill (Alexa-hosted, code from skill_model.py) posts each request to a
secret webhook. The answer goes straight back in the HTTP reply,
so Alexa speaks it at once, without a second trip through Alexa Media.
"""
from __future__ import annotations

from collections import deque
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

from .const import (
    CONF_DEFAULT_ECHO,
    CONF_DIALOG_PROMPT,
    CONF_GOODBYE_TEXT,
    CONF_INVOCATION_NAME,
    CONF_LATE_TEXT,
    CONF_RETRY_PROMPT,
    DEFAULT_DIALOG_PROMPT,
    DEFAULT_ECHO,
    DEFAULT_GOODBYE_TEXT,
    DEFAULT_INVOCATION_NAME,
    DEFAULT_LATE_TEXT,
    DEFAULT_RETRY_PROMPT,
    DOMAIN,
    SKILL_HELP_TEXT,
    SKILL_PHONE_LATER_TEXT,
)
from .skill_model import (
    INTENT_PHONE,
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

INTENTS_GOODBYE = ("AMAZON.StopIntent", "AMAZON.CancelIntent", "AMAZON.NoIntent")
INTENTS_SILENT_OK = ("AMAZON.NavigateHomeIntent", "AMAZON.YesIntent")

MAX_TEXT_LENGTH = 500
MAX_SPEECH_LENGTH = 7900
# The skill code gives Home Assistant 6.5 seconds, Amazon waits about 8
SKILL_BUDGET_SECONDS = 6.0
RATE_LIMIT_REQUESTS = 20
RATE_LIMIT_WINDOW_SECONDS = 60.0


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
        self._requests: deque[float] = deque()
        self._active = False
        self.last_request: dict[str, str] | None = None

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
        if not self._webhook_id:
            await self._async_new_webhook_id()

    async def _async_save(self) -> None:
        """Persist the secret, skill link and known Echos."""
        await self._store.async_save(
            {
                "webhook_id": self._webhook_id,
                "application_id": self._application_id,
                "devices": self._devices,
            }
        )

    async def _async_new_webhook_id(self) -> None:
        """Create a new secret, which invalidates the old skill code."""
        self._webhook_id = f"{DOMAIN}_{secrets.token_hex(24)}"
        self._application_id = None
        self._devices = {}
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

    def _echo_for(self, device_id: str | None) -> str:
        """Return the Echo entity for an Alexa device id, or the default Echo."""
        if device_id and device_id in self._devices:
            return self._devices[device_id]
        return str(self.entry.options.get(CONF_DEFAULT_ECHO, DEFAULT_ECHO))

    @staticmethod
    def _speech(
        text: str, end_session: bool = True, reprompt: str | None = None
    ) -> web.Response:
        """Return the reply the skill code turns into Alexa speech."""
        reply: dict[str, Any] = {
            "speech": text[:MAX_SPEECH_LENGTH],
            "end_session": end_session,
        }
        if reprompt and not end_session:
            reply["reprompt"] = reprompt[:MAX_SPEECH_LENGTH]
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
        if (
            not isinstance(application_id, str)
            or not application_id
            or action not in ACTIONS
            or not isinstance(text, str)
            or not isinstance(device_id, str | None)
            or not isinstance(intent, str | None)
            or (intent is not None and len(intent) > MAX_INTENT_LENGTH)
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

        if action == ACTION_LAUNCH:
            return self._ask_again(
                self._option(CONF_DIALOG_PROMPT, DEFAULT_DIALOG_PROMPT)
            )

        if action == ACTION_INTENT:
            question = question_from_intent(intent, text)
            if question is None:
                return self._answer_other_intent(intent)
        else:
            question = text

        question = " ".join(question.split())[:MAX_TEXT_LENGTH]
        if len(question) < 2:
            return self._ask_again(self._option(CONF_RETRY_PROMPT, DEFAULT_RETRY_PROMPT))

        return await self._async_ask(question, self._echo_for(device_id), start_time)

    def _answer_other_intent(self, intent: str | None) -> web.Response:
        """Answer intents that are not a question."""
        if intent in INTENTS_GOODBYE:
            return self._speech(self._option(CONF_GOODBYE_TEXT, DEFAULT_GOODBYE_TEXT))
        if intent == "AMAZON.HelpIntent":
            return self._ask_again(SKILL_HELP_TEXT)
        if intent == INTENT_PHONE:
            return self._speech(SKILL_PHONE_LATER_TEXT)
        if intent in INTENTS_SILENT_OK:
            return self._speech("Okay.")
        # AMAZON.FallbackIntent and anything unknown
        return self._ask_again(self._option(CONF_RETRY_PROMPT, DEFAULT_RETRY_PROMPT))

    def _option(self, key: str, default: str) -> str:
        """Return a text option, falling back to its default when empty."""
        return str(self.entry.options.get(key, default) or default)

    async def _async_ask(
        self, question: str, device: str, start_time: float
    ) -> web.Response:
        """Answer a question within the skill's time limit."""
        manager = self.manager
        self.last_request = {
            "time": dt_util.now().strftime("%d.%m. %H:%M:%S"),
            "text": question,
        }
        result = await manager.async_answer_within_budget(
            question,
            device,
            start_time=start_time,
            path=PATH_SKILL,
            budget=SKILL_BUDGET_SECONDS,
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
            return self._ask_again(self._option(CONF_RETRY_PROMPT, DEFAULT_RETRY_PROMPT))

        manager.add_history_entry(
            device,
            question,
            result.speech,
            duration=duration,
            char_count=len(result.speech),
            mode="Kurz",
            timing=f"KI {result.timing_text} • {PATH_SKILL}",
        )
        manager.record_query_stats(
            device=device,
            query=question,
            duration=duration,
            llm_seconds=result.llm_seconds,
            agent=result.agent,
            path=PATH_SKILL,
        )
        return self._speech(result.speech)
