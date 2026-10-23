"""The Schlaue Antworten integration."""
from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, ServiceCall, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_ANNOUNCE_MODEL,
    CONF_DEFAULT_ECHO,
    CONF_DIALOG_PROMPT,
    CONF_FALLBACK_AGENT,
    CONF_PRIMARY_AGENT,
    CONF_SHORT_ANSWERS,
    DEFAULT_ANNOUNCE_MODEL,
    DEFAULT_DIALOG_PROMPT,
    DEFAULT_ECHO,
    DEFAULT_FALLBACK_AGENT,
    DEFAULT_PRIMARY_AGENT,
    DEFAULT_SHORT_ANSWERS,
    DOMAIN,
    EVENT_ACTIONABLE_NOTIFICATION,
    EVENT_ID_QUERY,
    SERVICE_ASK_QUESTION,
    SERVICE_START_DIALOG,
    TRIGGER_BOOLEAN_ENTITY,
)

_LOGGER = logging.getLogger(__name__)

ERROR_PATTERNS = [
    "503",
    "service unavailable",
    "servererror",
    "high demand",
    "error talking",
    "api error",
    "rate limit",
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Schlaue Antworten from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    manager = SchlaueAntwortenManager(hass, entry)
    await manager.async_setup()
    hass.data[DOMAIN][entry.entry_id] = manager

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.entry_id in hass.data[DOMAIN]:
        manager: SchlaueAntwortenManager = hass.data[DOMAIN][entry.entry_id]
        await manager.async_unload()
        hass.data[DOMAIN].pop(entry.entry_id)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    return await async_setup_entry(hass, entry)


class SchlaueAntwortenManager:
    """Manager class for Schlaue Antworten logic."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the manager."""
        self.hass = hass
        self.entry = entry
        self._unsub_event: Any = None
        self._unsub_state: Any = None

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
        prompt = self.entry.options.get(CONF_DIALOG_PROMPT, DEFAULT_DIALOG_PROMPT)

        # Stop any active media playback first
        try:
            await self.hass.services.async_call(
                "media_player",
                "media_stop",
                {"entity_id": target_device},
                blocking=True,
            )
        except Exception:
            pass

        # Trigger actionable notification script or fallback
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
                blocking=True,
            )
        else:
            _LOGGER.warning(
                "script.activate_alexa_actionable_notification not found"
            )

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
        data = event.data
        if data.get("event_id") != EVENT_ID_QUERY:
            return

        raw_response = str(data.get("event_response", "")).strip()
        resp_lower = raw_response.lower()

        # Check for cancel or empty
        cancel_phrases = {
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
        }
        if not raw_response or resp_lower in cancel_phrases or len(raw_response) <= 1:
            _LOGGER.debug("Dialog cancelled or response empty: %s", raw_response)
            return

        # Identify reply Echo
        reply_device = (
            data.get("entity_id")
            or data.get("device")
            or self._get_target_echo()
        )

        await self.async_process_and_speak(raw_response, str(reply_device))

    async def async_process_and_speak(self, question: str, reply_device: str) -> None:
        """Query LLM and output answer via Alexa Media Player."""
        opts = self.entry.options
        primary_agent = opts.get(CONF_PRIMARY_AGENT, DEFAULT_PRIMARY_AGENT)
        fallback_agent = opts.get(CONF_FALLBACK_AGENT, DEFAULT_FALLBACK_AGENT)
        short_answers = opts.get(CONF_SHORT_ANSWERS, DEFAULT_SHORT_ANSWERS)
        announce_model = opts.get(CONF_ANNOUNCE_MODEL, DEFAULT_ANNOUNCE_MODEL)

        if short_answers:
            prompt = (
                "Bitte antworte kurz und prägnant in maximal 1 bis 2 Sätzen auf Deutsch "
                "für eine direkte Sprachausgabe ohne Aufzählungen, ohne Listen, "
                f"ohne Formatierungen und ohne Sonderzeichen auf folgende Frage: {question}"
            )
        else:
            prompt = question

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

        # 4. Final speech assembly
        if is_error or not raw_speech:
            final_speech = (
                "Die KI ist im Moment leider überlastet. "
                "Bitte versuche es in einem Moment noch einmal."
            )
        else:
            # Clean markdown formatting (*, #, `, _, ~)
            cleaned = re.sub(r"[*#`_~]", "", raw_speech).strip()
            if announce_model:
                agent_name = self._get_agent_display_name(used_agent)
                final_speech = f"{cleaned} Beantwortet von {agent_name}."
            else:
                final_speech = cleaned

        # 5. Output via notify.alexa_media
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

