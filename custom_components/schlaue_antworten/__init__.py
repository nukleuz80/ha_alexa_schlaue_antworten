"""The Schlaue Antworten integration."""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant, ServiceCall, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .answer import AnswerEngine, AnswerResult
from .const import (
    CONF_ABORT_PROMPT,
    CONF_ANSWER_BUDGET,
    CONF_DEFAULT_ECHO,
    CONF_DIALOG_PROMPT,
    CONF_DIRECT_QUERY_PREFIXES,
    CONF_ENABLE_DETAILED_FOLLOWUP,
    CONF_ENABLE_DIRECT_QUERY,
    CONF_ENABLE_LOGGING,
    CONF_FOLLOWUP_PROMPT,
    CONF_GOODBYE_TEXT,
    CONF_INTERACTIVE_CONFIRM_PROMPT,
    CONF_LATE_TEXT,
    CONF_MOBILE_CONFIRMATION,
    CONF_NOTIFY_TARGET,
    CONF_RETRY_PROMPT,
    CONF_VOICE_PATH,
    DEFAULT_ABORT_PROMPT,
    DEFAULT_ANSWER_BUDGET,
    DEFAULT_COMMUNITY_SKILL_ID,
    DEFAULT_DIALOG_PROMPT,
    DEFAULT_DIRECT_QUERY_PREFIXES,
    DEFAULT_ECHO,
    DEFAULT_ENABLE_DETAILED_FOLLOWUP,
    DEFAULT_ENABLE_DIRECT_QUERY,
    DEFAULT_ENABLE_LOGGING,
    DEFAULT_FOLLOWUP_PROMPT,
    DEFAULT_GOODBYE_TEXT,
    DEFAULT_INTERACTIVE_CONFIRM_PROMPT,
    DEFAULT_LATE_TEXT,
    DEFAULT_MOBILE_CONFIRMATION,
    DEFAULT_NOTIFY_TARGET,
    DEFAULT_RETRY_PROMPT,
    DEFAULT_VOICE_PATH,
    DOMAIN,
    ENTITY_ID_ACTIONABLE_INPUT_TEXT,
    EVENT_ACTIONABLE_NOTIFICATION,
    EVENT_ACTION_CONFIRMED,
    EVENT_ACTION_DECLINED,
    EVENT_ID_FOLLOWUP,
    EVENT_ID_INTERACTIVE,
    EVENT_ID_QUERY,
    FILLER_PHRASES,
    MOBILE_QUESTION_PHRASES,
    MOBILE_TRIGGER_PHRASES,
    SERVICE_ASK_QUESTION,
    SERVICE_INTERACTIVE_QUESTION,
    SERVICE_START_DIALOG,
    TRIGGER_BOOLEAN_ENTITY,
    VOICE_PATH_COMMUNITY,
    VOICE_PATH_SKILL,
)
from .claude_bridge import ClaudeBridge
from .skill import SkillConnector

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.BUTTON, Platform.SENSOR]

# Number of recent queries kept for the mean response time
RECENT_TIMINGS_MAX = 20

# How the question reached Schlaue Antworten, shown in the log and the sensor
PATH_DIRECT = "direkt"
PATH_DIALOG = "dialog"
PATH_SERVICE = "dienst"

RE_NON_WORDS = re.compile(r"[^\w\s]")

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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Schlaue Antworten from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    manager = SchlaueAntwortenManager(hass, entry)
    await manager.async_setup()
    hass.data[DOMAIN][entry.entry_id] = manager

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if entry.entry_id in hass.data[DOMAIN]:
        manager: SchlaueAntwortenManager = hass.data[DOMAIN][entry.entry_id]
        await manager.async_unload()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


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
        self._unsub_last_called: Any = None
        self._last_questions: dict[str, Any] = {}
        self._retry_counts: dict[str, int] = {}
        self._active_interactive: dict[str, dict[str, Any]] = {}
        self._history: list[dict[str, str]] = []
        self._stats_store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}_stats")
        self._stats: dict[str, Any] = {
            "date": dt_util.now().date().isoformat(),
            "today_count": 0,
            "today_short": 0,
            "today_detailed": 0,
            "total_count": 0,
            "last_query": None,
            "last_device": None,
            "last_time": None,
            "last_duration": None,
            "last_llm_seconds": None,
            "last_agent": None,
            "last_path": None,
            "recent": [],
        }
        self._stats_listeners: list[Callable[[], None]] = []
        self._unsub_midnight: Any = None
        self._pending_followup_tasks: dict[str, asyncio.Task[None]] = {}
        self.answers = AnswerEngine(hass, entry)
        self._background_tasks: set[asyncio.Task[Any]] = set()
        voice_path = entry.options.get(CONF_VOICE_PATH, DEFAULT_VOICE_PATH)
        self.uses_community = voice_path != VOICE_PATH_SKILL
        self.uses_skill = voice_path != VOICE_PATH_COMMUNITY
        self.skill = SkillConnector(hass, entry, self)
        self.claude = ClaudeBridge(hass, entry, self)

    def _cancel_pending_followup(self, device: str | None = None) -> None:
        """Cancel running delayed follow-up timer(s) immediately."""
        if device:
            task = self._pending_followup_tasks.pop(device, None)
            if task and not task.done():
                task.cancel()
        else:
            for dev, task in list(self._pending_followup_tasks.items()):
                if not task.done():
                    task.cancel()
            self._pending_followup_tasks.clear()

    async def _async_delayed_followup(
        self, reply_device: str, followup_prompt: str, wait_duration: float
    ) -> None:
        """Wait for TTS to finish and trigger actionable notification for follow-up."""
        try:
            await asyncio.sleep(wait_duration)

            # Check if user explicitly stopped playback on the Echo during the wait
            dev_state = self.hass.states.get(reply_device)
            if dev_state:
                summary = str(
                    dev_state.attributes.get("last_called_summary", "")
                ).lower().strip()
                if summary in ("stopp", "stop", "abbrechen", "abbruch", "aus", "pause"):
                    last_ts = dev_state.attributes.get("last_called_timestamp", 0)
                    if last_ts and (time.time() * 1000 - last_ts) < (wait_duration + 5.0) * 1000:
                        _LOGGER.info(
                            "User stopped playback on %s (summary: %s); cancelling follow-up",
                            reply_device,
                            summary,
                        )
                        return

            # Check if device is still reported as actively playing
            for _ in range(8):
                dev_state = self.hass.states.get(reply_device)
                if dev_state and dev_state.state == "playing":
                    await asyncio.sleep(0.5)
                else:
                    break

            # Buffer after playback finishes to allow Echo audio pipeline to reset
            await asyncio.sleep(0.6)

            _LOGGER.info(
                "Triggering actionable notification follow-up on %s: %s",
                reply_device,
                followup_prompt,
            )
            await self.async_trigger_actionable_notification(
                reply_device, followup_prompt, EVENT_ID_FOLLOWUP
            )
        except asyncio.CancelledError:
            _LOGGER.debug(
                "Delayed follow-up on %s was cancelled (new query or dialog initiated)",
                reply_device,
            )
        finally:
            self._pending_followup_tasks.pop(reply_device, None)

    def add_history_entry(
        self,
        device: str,
        query: str,
        output: str,
        duration: float | None = None,
        char_count: int | None = None,
        mode: str | None = None,
        timing: str | None = None,
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
        if timing:
            meta_parts.append(timing)

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
        if self.uses_community:
            # 1. Listen for Alexa Actionable Notification responses
            self._unsub_event = self.hass.bus.async_listen(
                EVENT_ACTIONABLE_NOTIFICATION, self._async_handle_notification_event
            )

            # 2. Listen for the input_boolean trigger (Scene/Routine compatibility)
            self._unsub_state = async_track_state_change_event(
                self.hass,
                [TRIGGER_BOOLEAN_ENTITY],
                self._async_handle_boolean_trigger,
            )

            # 3. Listen for direct voice queries (e.g. "schlaue frage ...")
            self._unsub_last_called = self.hass.bus.async_listen(
                "alexa_media_last_called_event",
                self._async_handle_last_called_event,
            )

        # The own skill gets its answer straight back through a webhook
        await self.skill.async_load()
        if self.uses_skill:
            self.skill.async_start()
        await self.claude.async_load()
        if self.uses_skill and self.claude.is_set_up:
            self.claude.async_start()

        # 4. Load persistent daily statistics
        stored_stats = await self._stats_store.async_load()
        if stored_stats and isinstance(stored_stats, dict):
            self._stats.update(stored_stats)
        self._check_date_rollover()

        # 5. Listen for midnight reset
        self._unsub_midnight = async_track_time_change(
            self.hass, self._async_handle_midnight_reset, hour=0, minute=0, second=0
        )

        # 6. Register services
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
        self.hass.services.async_register(
            DOMAIN,
            SERVICE_INTERACTIVE_QUESTION,
            self.async_service_interactive_question,
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

        if self._unsub_last_called:
            self._unsub_last_called()
            self._unsub_last_called = None

        if self._unsub_midnight:
            self._unsub_midnight()
            self._unsub_midnight = None

        self._cancel_pending_followup()
        self.skill.async_stop()
        self.claude.async_stop()

        for task in list(self._background_tasks):
            task.cancel()
        self._background_tasks.clear()

        self.hass.services.async_remove(DOMAIN, SERVICE_START_DIALOG)
        self.hass.services.async_remove(DOMAIN, SERVICE_ASK_QUESTION)
        self.hass.services.async_remove(DOMAIN, SERVICE_INTERACTIVE_QUESTION)

    @property
    def stats(self) -> dict[str, Any]:
        """Return the current stats dictionary."""
        return self._stats

    def register_stats_listener(
        self, listener: Callable[[], None]
    ) -> Callable[[], None]:
        """Register a callback for stats updates."""
        self._stats_listeners.append(listener)

        def _remove() -> None:
            if listener in self._stats_listeners:
                self._stats_listeners.remove(listener)

        return _remove

    def track_task(self, task: asyncio.Task[Any]) -> None:
        """Keep a background task until it ends; unloading cancels it."""
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    def notify_stats_listeners(self) -> None:
        """Notify all registered stats listeners of a state change."""
        self._notify_stats_listeners()

    def _notify_stats_listeners(self) -> None:
        """Notify all registered stats listeners of a state change."""
        for listener in self._stats_listeners:
            try:
                listener()
            except Exception as err:
                _LOGGER.warning("Error in stats listener: %s", err)

    def timing_summary(self) -> dict[str, float | None]:
        """Return the mean AI and total seconds over the recent queries."""
        recent = [
            item for item in self._stats.get("recent") or [] if isinstance(item, dict)
        ]
        if not recent:
            return {"llm": None, "total": None}
        return {
            "llm": round(sum(item["llm"] for item in recent) / len(recent), 2),
            "total": round(sum(item["total"] for item in recent) / len(recent), 2),
        }

    def _check_date_rollover(self) -> bool:
        """Check if date changed and reset daily counters if necessary."""
        today = dt_util.now().date().isoformat()
        if self._stats.get("date") != today:
            self._stats["date"] = today
            self._stats["today_count"] = 0
            self._stats["today_short"] = 0
            self._stats["today_detailed"] = 0
            return True
        return False

    @callback
    def _async_handle_midnight_reset(self, *args: Any) -> None:
        """Reset daily counters at midnight."""
        self._check_date_rollover()
        self.hass.async_create_task(self._stats_store.async_save(self._stats))
        self._notify_stats_listeners()

    def record_query_stats(
        self,
        device: str,
        query: str,
        is_followup: bool = False,
        duration: float | None = None,
        llm_seconds: float | None = None,
        agent: str | None = None,
        path: str | None = None,
    ) -> None:
        """Record query metrics and notify listeners."""
        self._check_date_rollover()
        self._stats["today_count"] = self._stats.get("today_count", 0) + 1
        self._stats["total_count"] = self._stats.get("total_count", 0) + 1
        if is_followup:
            self._stats["today_detailed"] = self._stats.get("today_detailed", 0) + 1
        else:
            self._stats["today_short"] = self._stats.get("today_short", 0) + 1

        clean_dev = device.replace("media_player.", "").replace("_", " ").title()
        self._stats["last_query"] = query
        self._stats["last_device"] = clean_dev
        self._stats["last_time"] = dt_util.now().isoformat()
        if duration is not None:
            self._stats["last_duration"] = round(duration, 1)
        self._stats["last_llm_seconds"] = (
            round(llm_seconds, 2) if llm_seconds is not None else None
        )
        self._stats["last_agent"] = agent
        self._stats["last_path"] = path
        if duration is not None and llm_seconds is not None:
            recent = [
                item
                for item in self._stats.get("recent") or []
                if isinstance(item, dict)
            ]
            recent.append(
                {
                    "time": dt_util.now().isoformat(timespec="seconds"),
                    "agent": agent,
                    "path": path,
                    "llm": round(llm_seconds, 2),
                    "total": round(duration, 2),
                }
            )
            self._stats["recent"] = recent[-RECENT_TIMINGS_MAX:]

        # Save to storage in background
        self.hass.async_create_task(self._stats_store.async_save(self._stats))
        self._notify_stats_listeners()

    def _resolve_echo_from_event(self, event_data: dict[str, Any]) -> str:
        """Resolve the exact media_player entity from an Alexa event payload."""
        # 1. Direct entity_id if provided and valid
        eid = event_data.get("entity_id")
        if eid and self.hass.states.get(str(eid)):
            return str(eid)

        dev = event_data.get("device")
        if dev and self.hass.states.get(str(dev)):
            return str(dev)

        # 2. Match by serial / unique_id in entity registry (exact for alexa_media last_called)
        serial = event_data.get("last_called")
        if serial:
            ent_reg = er.async_get(self.hass)
            for entity in ent_reg.entities.values():
                if entity.platform == "alexa_media" and entity.unique_id == str(serial):
                    return entity.entity_id

        # 3. Match by friendly name in states
        name = event_data.get("name")
        if name:
            for state in self.hass.states.async_all("media_player"):
                if state.attributes.get("friendly_name") == name:
                    return state.entity_id

        # 4. Fallback to standard target Echo detection
        return self._get_target_echo()

    def _get_target_echo(self, preferred_device: str | None = None) -> str:
        """Determine the active Echo media_player."""
        if preferred_device and self.hass.states.get(preferred_device):
            return preferred_device

        # Check existing sensor.last_alexa for full backward compatibility
        last_alexa = self.hass.states.get("sensor.last_alexa")
        if (
            last_alexa
            and last_alexa.state
            and last_alexa.state not in ("unknown", "unavailable", "")
        ):
            return last_alexa.state

        # Zero-YAML: Auto-detect active Echo directly from media_player entities
        for state in self.hass.states.async_all("media_player"):
            if state.attributes.get("last_called") is True:
                return state.entity_id

        default_echo = self.entry.options.get(CONF_DEFAULT_ECHO, DEFAULT_ECHO)
        return str(default_echo)

    async def async_trigger_actionable_notification(
        self,
        target_device: str,
        text: str,
        event_id: str,
    ) -> None:
        """Trigger an Alexa Actionable Notification directly (Zero-YAML) or via script."""
        clean_text = text.replace('"', "'").replace("&", " und ").replace("\\", "")
        # Protect against Home Assistant input_text 255 character limit
        if len(clean_text) > 175:
            clean_text = clean_text[:172] + "..."
        if self.hass.services.has_service(
            "script", "activate_alexa_actionable_notification"
        ):
            await self.hass.services.async_call(
                "script",
                "activate_alexa_actionable_notification",
                {
                    "text": clean_text,
                    "event_id": event_id,
                    "alexa_device": target_device,
                    "suppress_confirmation": "true",
                },
                blocking=False,
            )
            return

        # Direct Zero-YAML execution without YAML script
        payload = json.dumps({
            "text": clean_text,
            "event": event_id,
            "suppress_confirmation": "true",
        })

        if self.hass.services.has_service("input_text", "set_value"):
            try:
                await self.hass.services.async_call(
                    "input_text",
                    "set_value",
                    {
                        "entity_id": ENTITY_ID_ACTIONABLE_INPUT_TEXT,
                        "value": payload,
                    },
                    blocking=True,
                )
            except Exception as err:
                _LOGGER.debug(
                    "input_text.set_value failed, setting state directly: %s", err
                )
                self.hass.states.async_set(ENTITY_ID_ACTIONABLE_INPUT_TEXT, payload)
        else:
            self.hass.states.async_set(ENTITY_ID_ACTIONABLE_INPUT_TEXT, payload)

        try:
            await self.hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": target_device,
                    "media_content_type": "skill",
                    "media_content_id": DEFAULT_COMMUNITY_SKILL_ID,
                },
                blocking=False,
            )
        except Exception as err:
            _LOGGER.error(
                "Failed to trigger actionable notification skill on %s: %s",
                target_device,
                err,
            )

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

    async def async_service_interactive_question(self, call: ServiceCall) -> None:
        """Service handler to ask a proactive interactive question for automations."""
        question = call.data.get("question", "").strip()
        if not question:
            return

        target_device = self._get_target_echo(call.data.get("echo_device"))
        event_id = str(call.data.get("event_id", "interactive_question") or "interactive_question").strip()
        await self.async_interactive_question(question, target_device, event_id)

    async def async_interactive_question(
        self, question: str, target_device: str, custom_event_id: str
    ) -> None:
        """Ask a proactive interactive question on an Echo device."""
        self._cancel_pending_followup(target_device)
        self._active_interactive[target_device] = {
            "question": question,
            "event_id": custom_event_id,
        }

        # Stop active media playback if currently playing
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

        # Trigger actionable notification with EVENT_ID_INTERACTIVE
        await self.async_trigger_actionable_notification(
            target_device, question, EVENT_ID_INTERACTIVE
        )

    async def async_answer_within_budget(
        self,
        question: str,
        reply_device: str,
        *,
        is_followup: bool = False,
        previous_answer: str = "",
        start_time: float,
        path: str,
        budget: float | None = None,
        answer_task: asyncio.Task[AnswerResult] | None = None,
    ) -> AnswerResult | None:
        """Answer within the time budget, or return None and push the answer later.

        The AI keeps working after the budget ran out. Its answer then goes to
        the phone, so the caller only has to say the late text. A given budget
        caps the configured one, as the own skill must reply within seconds.
        A running answer task, started ahead of time, is awaited instead of
        asking the AI again.
        """
        if answer_task is None:
            answer_task = self.hass.async_create_task(
                self.answers.async_answer(
                    question,
                    reply_device,
                    is_followup=is_followup,
                    previous_answer=previous_answer,
                    start_time=start_time,
                    path=path,
                )
            )
        configured = float(
            self.entry.options.get(CONF_ANSWER_BUDGET, DEFAULT_ANSWER_BUDGET) or 0
        )
        if budget is None:
            budget = configured
        elif configured > 0:
            budget = min(budget, configured)
        task = answer_task
        if budget <= 0:
            return await task

        remaining = max(budget - (time.monotonic() - start_time), 0.1)
        done, _pending = await asyncio.wait({task}, timeout=remaining)
        if done:
            return task.result()

        _LOGGER.info(
            "No answer within the budget of %.1fs (%s); the answer follows by push",
            budget,
            path,
        )
        late = self.hass.async_create_task(
            self._async_deliver_late(
                question, reply_device, task, start_time, path, is_followup
            )
        )
        # Both are tracked, so unloading stops the AI request as well
        for background in (task, late):
            self.track_task(background)
        return None

    async def _async_deliver_late(
        self,
        question: str,
        reply_device: str,
        task: asyncio.Task[AnswerResult],
        start_time: float,
        path: str,
        is_followup: bool = False,
    ) -> None:
        """Wait for an answer that missed the budget and push it to the phone."""
        result = await task
        duration = time.monotonic() - start_time
        label = f"[Spät] {'[Vertiefung] ' if is_followup else ''}{question}"
        if result.error or result.unclear or not result.text:
            _LOGGER.info("The late answer to %r brought no usable text", question)
            self.add_history_entry(
                reply_device,
                label,
                "Keine Antwort",
                duration=duration,
                mode="Fehler",
                timing=result.timing_text,
            )
            return
        await self.async_send_to_mobile(
            question=question,
            answer=result.text,
            reply_device=reply_device,
            confirm=False,
        )
        self.add_history_entry(
            reply_device,
            label,
            result.text,
            duration=duration,
            char_count=len(result.text),
            mode="Push",
            timing=f"KI {result.timing_text} • {path}",
        )
        self.record_query_stats(
            device=reply_device,
            query=question,
            is_followup=is_followup,
            duration=duration,
            llm_seconds=result.llm_seconds,
            agent=result.agent,
            path=path,
        )

    async def async_send_to_mobile(
        self, question: str, answer: str, reply_device: str, confirm: bool = True
    ) -> None:
        """Send an answer to the configured smartphone / notify target."""
        notify_target = str(
            self.entry.options.get(CONF_NOTIFY_TARGET, DEFAULT_NOTIFY_TARGET) or DEFAULT_NOTIFY_TARGET
        )
        confirm_text = str(
            self.entry.options.get(
                CONF_MOBILE_CONFIRMATION, DEFAULT_MOBILE_CONFIRMATION
            ) or ""
        )

        title = f"Schlaue Antworten: {question}"[:100]
        message = answer

        domain = "notify"
        service = (
            notify_target.replace("notify.", "")
            if notify_target.startswith("notify.")
            else notify_target
        )

        _LOGGER.info("Sending push notification to %s: %s", notify_target, title)
        try:
            await self.hass.services.async_call(
                domain,
                service,
                {"title": title, "message": message},
                blocking=False,
            )
        except Exception as err:
            _LOGGER.warning(
                "Could not send mobile notification to %s: %s", notify_target, err
            )

        if not confirm:
            return

        if confirm_text:
            try:
                await self.hass.services.async_call(
                    "notify",
                    "alexa_media",
                    {
                        "target": [reply_device],
                        "data": {"type": "tts"},
                        "message": confirm_text,
                    },
                    blocking=False,
                )
            except Exception as err:
                _LOGGER.error("Failed to speak mobile confirmation: %s", err)

        self.add_history_entry(
            reply_device,
            f"[Smartphone] {question}",
            confirm_text or "Gesendet",
            char_count=len(answer),
            mode="Push",
        )

    async def async_start_dialog(self, target_device: str) -> None:
        """Start the Actionable Notification dialog on the target Echo."""
        self._cancel_pending_followup(target_device)
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

        # Trigger actionable notification (non-blocking for immediate execution)
        await self.async_trigger_actionable_notification(
            target_device, prompt, EVENT_ID_QUERY
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
        self._cancel_pending_followup(reply_device)
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
            await self.async_trigger_actionable_notification(
                reply_device, retry_prompt, EVENT_ID_QUERY
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

    async def _async_handle_last_called_event(self, event: Event) -> None:
        """Handle direct voice queries spoken to Alexa in one sentence."""
        if not self.entry.options.get(
            CONF_ENABLE_DIRECT_QUERY, DEFAULT_ENABLE_DIRECT_QUERY
        ):
            return

        summary = str(event.data.get("summary", "")).strip()
        if not summary or len(summary) < 4:
            return

        summary_lower = summary.lower()

        # Collision guard: Ignore commands intended for starting the interactive routine or brainstorm
        if summary_lower in (
            "öffne schlaue antworten",
            "starte schlaue antworten",
            "schlaue antworten öffnen",
            "schlaue antworten starten",
            "schlaue antworten",
            "öffne brainstorm",
            "starte brainstorm",
        ) or summary_lower.startswith(("öffne schlaue antworten", "starte schlaue antworten")):
            return

        # Fetch configured prefixes (ordered longest first to prevent prefix shadowing)
        prefixes_str = str(
            self.entry.options.get(
                CONF_DIRECT_QUERY_PREFIXES, DEFAULT_DIRECT_QUERY_PREFIXES
            )
            or DEFAULT_DIRECT_QUERY_PREFIXES
        )
        prefixes = sorted(
            [p.strip().lower() for p in prefixes_str.split(",") if p.strip()],
            key=len,
            reverse=True,
        )

        matched_prefix: str | None = None
        for prefix in prefixes:
            if (
                summary_lower.startswith(prefix + " ")
                or summary_lower.startswith(prefix + ":")
                or summary_lower.startswith(prefix + ",")
            ):
                matched_prefix = prefix
                break

        if not matched_prefix:
            return

        # Extract the question, stripping prefix and leading punctuation
        cleaned_question = summary[len(matched_prefix):].lstrip(" :,?-").strip()
        if len(cleaned_question) < 3:
            return

        # Determine target Echo from event directly (serial/name mapping)
        reply_device = self._resolve_echo_from_event(event.data)

        _LOGGER.info(
            "Direct voice query matched prefix '%s' on %s: %s",
            matched_prefix,
            reply_device,
            cleaned_question,
        )

        self._cancel_pending_followup(reply_device)

        # Unconditionally stop any active speech or playback on the target Echo immediately
        try:
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "media_player",
                    "media_stop",
                    {"entity_id": reply_device},
                    blocking=False,
                )
            )
        except Exception as err:
            _LOGGER.debug("Immediate media_stop ignored: %s", err)

        # Process and speak answer directly (direct queries speak in one rut without interactive follow-up)
        await self.async_process_and_speak(
            cleaned_question,
            reply_device,
            is_followup=False,
            enable_followup_override=False,
            path=PATH_DIRECT,
        )

    async def _async_handle_notification_event(self, event: Event) -> None:
        """Process user's spoken answer from Actionable Notifications."""
        start_time = time.monotonic()
        data = event.data
        event_id = data.get("event_id")
        if event_id not in (EVENT_ID_QUERY, EVENT_ID_FOLLOWUP, EVENT_ID_INTERACTIVE):
            return

        raw_response = str(data.get("event_response", "")).strip()
        resp_lower = raw_response.lower()
        response_type = str(data.get("event_response_type", "")).strip()

        # Identify reply Echo
        reply_device = self._resolve_echo_from_event(data)
        self._cancel_pending_followup(reply_device)

        # Handle proactive interactive question response (e.g. from automations)
        if event_id == EVENT_ID_INTERACTIVE:
            stored_data = self._active_interactive.pop(reply_device, None)
            custom_event_id = (
                str(stored_data.get("event_id", "interactive_question"))
                if stored_data
                else "interactive_question"
            )
            question_text = (
                str(stored_data.get("question", ""))
                if stored_data
                else ""
            )

            is_positive = response_type == "ResponseYes" or any(
                p in resp_lower for p in POSITIVE_PHRASES
            )
            is_negative = response_type == "ResponseNo" or any(
                p in resp_lower for p in NEGATIVE_PHRASES
            )

            if is_positive:
                _LOGGER.info(
                    "Interactive action CONFIRMED for %s on %s (response: %s)",
                    custom_event_id,
                    reply_device,
                    raw_response,
                )
                self.hass.bus.async_fire(
                    EVENT_ACTION_CONFIRMED,
                    {
                        "confirmed": True,
                        "response_type": "ResponseYes",
                        "raw_response": raw_response,
                        "event_id": custom_event_id,
                        "echo_device": reply_device,
                        "question": question_text,
                    },
                )
                confirm_prompt = str(
                    self.entry.options.get(
                        CONF_INTERACTIVE_CONFIRM_PROMPT,
                        DEFAULT_INTERACTIVE_CONFIRM_PROMPT,
                    )
                    or DEFAULT_INTERACTIVE_CONFIRM_PROMPT
                )
                self.add_history_entry(
                    reply_device,
                    f"[Interaktiv] {question_text}",
                    confirm_prompt,
                    duration=time.monotonic() - start_time,
                    char_count=len(confirm_prompt),
                    mode="Bestätigt",
                )
                if confirm_prompt:
                    try:
                        await self.hass.services.async_call(
                            "notify",
                            "alexa_media",
                            {
                                "target": [reply_device],
                                "data": {"type": "tts"},
                                "message": confirm_prompt,
                            },
                            blocking=False,
                        )
                    except Exception as err:
                        _LOGGER.error("Failed to speak confirm prompt: %s", err)
            elif is_negative:
                _LOGGER.info(
                    "Interactive action DECLINED for %s on %s (response: %s)",
                    custom_event_id,
                    reply_device,
                    raw_response,
                )
                self.hass.bus.async_fire(
                    EVENT_ACTION_DECLINED,
                    {
                        "confirmed": False,
                        "response_type": "ResponseNo",
                        "raw_response": raw_response,
                        "event_id": custom_event_id,
                        "echo_device": reply_device,
                        "question": question_text,
                    },
                )
                goodbye_text = str(
                    self.entry.options.get(
                        CONF_GOODBYE_TEXT, DEFAULT_GOODBYE_TEXT
                    )
                    or DEFAULT_GOODBYE_TEXT
                )
                self.add_history_entry(
                    reply_device,
                    f"[Interaktiv] {question_text}",
                    goodbye_text,
                    duration=time.monotonic() - start_time,
                    char_count=len(goodbye_text),
                    mode="Abgelehnt",
                )
                if goodbye_text:
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
                        _LOGGER.error("Failed to speak decline prompt: %s", err)
            return

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

            # Check if user requested mobile push (e.g. "aufs Handy", "schick mir das")
            if any(p in resp_lower for p in MOBILE_TRIGGER_PHRASES):
                _LOGGER.info(
                    "User requested answer to be sent to smartphone for: %s",
                    stored_question,
                )
                await self.async_send_to_mobile(
                    question=stored_question,
                    answer=previous_answer,
                    reply_device=reply_device,
                )
                return

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
                    path=PATH_DIALOG,
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
            raw_response,
            reply_device,
            is_followup=False,
            start_time=start_time,
            path=PATH_DIALOG,
        )

    async def async_process_and_speak(
        self,
        question: str,
        reply_device: str,
        is_followup: bool = False,
        previous_answer: str = "",
        start_time: float | None = None,
        enable_followup_override: bool | None = None,
        path: str = PATH_SERVICE,
    ) -> None:
        """Query LLM and output answer via Alexa."""
        self._cancel_pending_followup(reply_device)
        if start_time is None:
            start_time = time.monotonic()

        opts = self.entry.options
        if enable_followup_override is not None:
            enable_followup = enable_followup_override
        else:
            enable_followup = opts.get(
                CONF_ENABLE_DETAILED_FOLLOWUP, DEFAULT_ENABLE_DETAILED_FOLLOWUP
            )
        followup_prompt = opts.get(
            CONF_FOLLOWUP_PROMPT, DEFAULT_FOLLOWUP_PROMPT
        )

        result = await self.async_answer_within_budget(
            question,
            reply_device,
            is_followup=is_followup,
            previous_answer=previous_answer,
            start_time=start_time,
            path=path,
        )

        # Too slow: say so now, the answer follows on the phone
        if result is None:
            late_text = str(
                opts.get(CONF_LATE_TEXT, DEFAULT_LATE_TEXT) or DEFAULT_LATE_TEXT
            )
            try:
                await self.hass.services.async_call(
                    "notify",
                    "alexa_media",
                    {
                        "target": [reply_device],
                        "data": {"type": "tts"},
                        "message": late_text,
                    },
                    blocking=False,
                )
            except Exception as err:
                _LOGGER.error("Failed to speak late text via notify.alexa_media: %s", err)
            return

        timing_text = result.timing_text

        # Error response
        if result.error:
            final_speech = result.speech
            duration = time.monotonic() - start_time
            self.add_history_entry(
                reply_device,
                question,
                final_speech,
                duration=duration,
                char_count=len(final_speech),
                mode="Fehler",
                timing=timing_text,
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

        # AI deemed the query unclear or nonsensical
        if result.unclear:
            await self._async_handle_unclear_query(
                reply_device, start_time=start_time
            )
            return

        # Query was successful and understood -> clear retry counter
        self._retry_counts.pop(reply_device, None)

        cleaned = result.text
        final_speech = result.speech
        used_agent = result.agent
        llm_seconds = result.llm_seconds

        # Check if user explicitly asked for mobile delivery in the question
        q_lower = question.lower()
        if any(p in q_lower for p in MOBILE_QUESTION_PHRASES):
            await self.async_send_to_mobile(
                question=question,
                answer=cleaned,
                reply_device=reply_device,
            )

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
            timing=f"KI {timing_text} • {path}",
        )
        self.record_query_stats(
            device=reply_device,
            query=question,
            is_followup=is_followup,
            duration=duration,
            llm_seconds=llm_seconds,
            agent=used_agent,
            path=path,
        )

        # 7. Actionable Notification with follow-up question if enabled
        if not is_followup and enable_followup:
            self._last_questions[reply_device] = {
                "question": question,
                "short_answer": cleaned,
            }
            combined_message = f"{final_speech} {followup_prompt}"

            # If message is compact (<= 175 chars), Alexa can speak answer + followup in one single notification
            if len(combined_message) <= 175:
                _LOGGER.info(
                    "Combined message length (%d chars) <= 175; sending single actionable notification to %s",
                    len(combined_message),
                    reply_device,
                )
                await self.async_trigger_actionable_notification(
                    reply_device, combined_message, EVENT_ID_FOLLOWUP
                )
                return

            # For answers exceeding 175 chars:
            # Speak answer via TTS first to avoid 255-char input_text limit,
            # then reliably schedule follow-up question with open microphone.
            _LOGGER.info(
                "Combined message length (%d chars) > 175; speaking answer via TTS and scheduling follow-up prompt",
                len(combined_message),
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
                _LOGGER.error("Failed to speak answer via notify.alexa_media: %s", err)
                return

            # Realistic German speech rate (~11.0 chars/s) + 1.8s cloud startup/latency buffer
            wait_duration = max(3.0, (len(final_speech) / 11.0) + 1.8)
            _LOGGER.debug(
                "Scheduling delayed follow-up prompt on %s in %.1f seconds",
                reply_device,
                wait_duration,
            )
            task = self.hass.async_create_task(
                self._async_delayed_followup(
                    reply_device, followup_prompt, wait_duration
                )
            )
            self._pending_followup_tasks[reply_device] = task
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
