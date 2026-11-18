"""Hand voice prompts from the own Alexa skill to a Claude Code session.

A small bridge on another machine types the prompt into a running Claude Code
session. When Claude has answered, a hook in that session posts the answer to
a local webhook here, and the Echo that asked speaks its first part.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import StrEnum
import logging
import re
import secrets
import time
from typing import TYPE_CHECKING, Any

import aiohttp
from aiohttp import hdrs, web

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.network import NoURLAvailableError, get_url
from homeassistant.helpers.storage import Store

from .const import (
    CLAUDE_REST_TEXT,
    CONF_CLAUDE_ECHOS,
    CONF_CLAUDE_TOKEN,
    CONF_CLAUDE_URL,
    DOMAIN,
)

if TYPE_CHECKING:
    from . import SchlaueAntwortenManager

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = f"{DOMAIN}_claude"
STORAGE_VERSION = 1

SEND_TIMEOUT_SECONDS = 4.0
# An answer is only spoken if Alexa sent a prompt within this time
PENDING_SECONDS = 30 * 60.0
RATE_LIMIT_PROMPTS = 6
RATE_LIMIT_WINDOW_SECONDS = 10 * 60.0
MAX_PROMPT_LENGTH = 500
MAX_ANSWER_LENGTH = 20000
MAX_SPOKEN_LENGTH = 400

RE_CODE_BLOCK = re.compile(r"```.*?```", re.DOTALL)
RE_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
RE_EMPHASIS = re.compile(r"[*`]+")
RE_MARKUP = re.compile(r"[#>|]+")
RE_SENTENCE_END = re.compile(r"(?<=[.!?])\s")


MAIN_SESSION = "alexa"
MAX_NAME_LENGTH = 20
# Spoken words that mean the main session
MAIN_SESSION_WORDS = ("alexa", "haupt", "hauptsitzung", "standard")
UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
RE_NOT_NAME = re.compile(r"[^a-z0-9]+")


class SendResult(StrEnum):
    """Outcome of a request to the Claude bridge."""

    SENT = "sent"
    OFF = "off"
    NOT_SET_UP = "not_set_up"
    NOT_ALLOWED = "not_allowed"
    BUSY = "busy"
    UNREACHABLE = "unreachable"
    CREATED = "created"
    SWITCHED = "switched"
    ENDED = "ended"
    UNKNOWN_SESSION = "unknown_session"
    TOO_MANY = "too_many"
    MAIN_SESSION = "main_session"
    NO_NAME = "no_name"
    LISTED = "listed"


@dataclass
class PendingPrompt:
    """A prompt whose answer an Echo is waiting for."""

    echo: str
    prompt: str
    sent: float


@dataclass
class BridgeReply:
    """What the bridge did, for the spoken reply."""

    result: SendResult
    session: str = ""
    sessions: list[str] | None = None
    active: str = ""
    with_prompt: bool = False


def session_name(spoken: str) -> str:
    """Return a session name from spoken words ("Heizung" -> "heizung")."""
    words = spoken.lower().split()
    if not words:
        return ""
    if words[0] in MAIN_SESSION_WORDS:
        return MAIN_SESSION
    name = RE_NOT_NAME.sub("-", words[0].translate(UMLAUTS)).strip("-")
    return name[:MAX_NAME_LENGTH]


def split_new_session(spoken: str) -> tuple[str, str]:
    """Split "heizung prüf das bad" into name and first prompt."""
    words = " ".join(spoken.split()).split(" ", 1)
    name = session_name(words[0]) if words[0] else ""
    return name, words[1] if len(words) > 1 else ""


def spoken_part(answer: str) -> str:
    """Return the first paragraph of an answer as plain, speakable text."""
    text = RE_CODE_BLOCK.sub(" ", answer)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    first = paragraphs[0] if paragraphs else ""
    first = RE_LINK.sub(r"\1", first)
    first = RE_EMPHASIS.sub("", first)
    first = " ".join(RE_MARKUP.sub(" ", first).split())
    if len(first) <= MAX_SPOKEN_LENGTH:
        return first
    cut = first[:MAX_SPOKEN_LENGTH]
    ends = [match.start() for match in RE_SENTENCE_END.finditer(cut)]
    return cut[: ends[-1]] if ends else cut.rsplit(" ", 1)[0] + " …"


class ClaudeBridge:
    """Send prompts to the Claude bridge and speak the answers."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        manager: SchlaueAntwortenManager,
    ) -> None:
        """Initialize the bridge."""
        self.hass = hass
        self.entry = entry
        self.manager = manager
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._webhook_id = ""
        self._enabled = True
        self._active = False
        self._sent: deque[float] = deque()
        self._pending: dict[str, PendingPrompt] = {}
        self.last_prompt: dict[str, str] | None = None

    @property
    def url(self) -> str:
        """Return the bridge address without a trailing slash."""
        return str(self.entry.options.get(CONF_CLAUDE_URL) or "").strip().rstrip("/")

    @property
    def token(self) -> str:
        """Return the shared secret for the bridge."""
        return str(self.entry.options.get(CONF_CLAUDE_TOKEN) or "").strip()

    @property
    def allowed_echos(self) -> list[str]:
        """Return the Echos that may send prompts."""
        echos = self.entry.options.get(CONF_CLAUDE_ECHOS) or []
        return [str(echo) for echo in echos] if isinstance(echos, list) else []

    @property
    def is_set_up(self) -> bool:
        """Return whether address and secret are configured."""
        return bool(self.url and self.token)

    @property
    def enabled(self) -> bool:
        """Return whether the bridge switch is on."""
        return self._enabled

    async def async_set_enabled(self, enabled: bool) -> None:
        """Turn the bridge on or off and remember it."""
        self._enabled = enabled
        if not enabled:
            self._pending.clear()
        await self._async_save()

    async def async_load(self) -> None:
        """Load the reply webhook id and the switch state."""
        data = await self._store.async_load() or {}
        self._webhook_id = str(data.get("webhook_id") or "")
        self._enabled = bool(data.get("enabled", True))
        if not self._webhook_id:
            self._webhook_id = f"{DOMAIN}_claude_{secrets.token_hex(24)}"
            await self._async_save()

    async def _async_save(self) -> None:
        """Persist the reply webhook id and the switch state."""
        await self._store.async_save(
            {"webhook_id": self._webhook_id, "enabled": self._enabled}
        )

    @callback
    def async_start(self) -> None:
        """Accept answers from the Claude session (local network only)."""
        if self._active:
            return
        webhook.async_register(
            self.hass,
            DOMAIN,
            "Schlaue Antworten Claude-Antwort",
            self._webhook_id,
            self._async_handle_answer,
            local_only=True,
            allowed_methods=[hdrs.METH_POST],
        )
        self._active = True

    @callback
    def async_stop(self) -> None:
        """Stop accepting answers."""
        if self._active:
            webhook.async_unregister(self.hass, self._webhook_id)
            self._active = False
        self._pending.clear()

    def reply_url(self) -> str:
        """Return the local address the Claude session posts answers to.

        Raises NoURLAvailableError if Home Assistant has no local address.
        """
        base_url = get_url(self.hass, allow_external=False, allow_cloud=False)
        return f"{base_url}{webhook.async_generate_path(self._webhook_id)}"

    def _rate_limited(self) -> bool:
        """Return True if too many prompts went out recently."""
        now = time.monotonic()
        while self._sent and now - self._sent[0] > RATE_LIMIT_WINDOW_SECONDS:
            self._sent.popleft()
        return len(self._sent) >= RATE_LIMIT_PROMPTS

    def _echo_name(self, echo: str) -> str:
        """Return the friendly name of an Echo."""
        state = self.hass.states.get(echo)
        return str(state.attributes.get("friendly_name") or echo) if state else echo

    def _check(self, echo: str | None) -> SendResult | None:
        """Return why an Echo may not reach Claude now, or None if it may."""
        if not self.is_set_up:
            return SendResult.NOT_SET_UP
        if not self._enabled:
            return SendResult.OFF
        if not echo or echo not in self.allowed_echos:
            return SendResult.NOT_ALLOWED
        if self._rate_limited():
            return SendResult.BUSY
        return None

    async def _async_request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> tuple[int, dict[str, Any]]:
        """Call the bridge; status 0 means it was not reachable."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.request(
                method,
                f"{self.url}{path}",
                json=payload,
                headers={hdrs.AUTHORIZATION: f"Bearer {self.token}"},
                timeout=aiohttp.ClientTimeout(total=SEND_TIMEOUT_SECONDS),
            ) as response:
                try:
                    data = await response.json(content_type=None)
                except ValueError:
                    data = {}
                return response.status, data if isinstance(data, dict) else {}
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.warning("Claude bridge not reachable: %s", err)
            return 0, {}

    def _prompt_payload(self, prompt: str, echo: str) -> dict[str, Any]:
        """Return text and reply address for a prompt.

        Raises NoURLAvailableError if Home Assistant has no local address.
        """
        return {
            "text": f"[Alexa · {self._echo_name(echo)}] {prompt}",
            "reply_url": self.reply_url(),
        }

    def _note_prompt(self, session: str, prompt: str, echo: str) -> None:
        """Remember that an Echo waits for the answer of a session."""
        self._sent.append(time.monotonic())
        self._pending[session] = PendingPrompt(echo, prompt, time.monotonic())
        self.last_prompt = {"echo": echo, "text": f"[{session}] {prompt}"}
        self.manager.add_history_entry(
            echo, f"[Claude {session}] {prompt}", "An Claude geschickt", mode="Claude"
        )

    async def async_send(self, prompt: str, echo: str | None) -> SendResult:
        """Hand a spoken prompt to the active Claude session.

        Only Echos that are assigned and allowed may send; the answer later
        goes back to the same Echo.
        """
        return (await self.async_send_reply(prompt, echo)).result

    async def async_send_reply(self, prompt: str, echo: str | None) -> BridgeReply:
        """Hand a spoken prompt to the active session and say where it went."""
        if (refused := self._check(echo)) is not None or echo is None:
            return BridgeReply(refused or SendResult.NOT_ALLOWED)
        prompt = " ".join(prompt.split())[:MAX_PROMPT_LENGTH]
        try:
            payload = self._prompt_payload(prompt, echo)
        except NoURLAvailableError:
            _LOGGER.error("Home Assistant has no local address for Claude's answer")
            return BridgeReply(SendResult.UNREACHABLE)
        status, data = await self._async_request("POST", "/prompt", payload)
        if status != 200:
            _LOGGER.warning("Claude bridge answered HTTP %s", status)
            return BridgeReply(SendResult.UNREACHABLE)
        session = str(data.get("session") or MAIN_SESSION)
        self._note_prompt(session, prompt, echo)
        return BridgeReply(SendResult.SENT, session=session)

    async def async_new_session(self, spoken: str, echo: str | None) -> BridgeReply:
        """Start a new Claude session, optionally with a first prompt."""
        if (refused := self._check(echo)) is not None or echo is None:
            return BridgeReply(refused or SendResult.NOT_ALLOWED)
        name, prompt = split_new_session(spoken)
        prompt = prompt[:MAX_PROMPT_LENGTH]
        if not name:
            return BridgeReply(SendResult.NO_NAME)
        if name == MAIN_SESSION:
            return BridgeReply(SendResult.MAIN_SESSION, session=name)
        payload: dict[str, Any] = {"name": name}
        if prompt:
            try:
                payload.update(self._prompt_payload(prompt, echo))
            except NoURLAvailableError:
                return BridgeReply(SendResult.UNREACHABLE)
        status, data = await self._async_request("POST", "/sessions", payload)
        if status == 409:
            return BridgeReply(
                SendResult.TOO_MANY, sessions=list(data.get("sessions") or [])
            )
        if status != 200:
            return BridgeReply(SendResult.UNREACHABLE)
        name = str(data.get("session") or name)
        if prompt:
            self._note_prompt(name, prompt, echo)
        else:
            self._sent.append(time.monotonic())
        return BridgeReply(SendResult.CREATED, session=name, with_prompt=bool(prompt))

    async def async_switch(self, spoken: str, echo: str | None) -> BridgeReply:
        """Send the following prompts to another session."""
        if (refused := self._check(echo)) is not None:
            return BridgeReply(refused)
        name = session_name(spoken)
        if not name:
            return BridgeReply(SendResult.NO_NAME)
        status, data = await self._async_request("POST", "/switch", {"name": name})
        if status == 404:
            return BridgeReply(
                SendResult.UNKNOWN_SESSION,
                session=name,
                sessions=list(data.get("sessions") or []),
            )
        if status != 200:
            return BridgeReply(SendResult.UNREACHABLE)
        return BridgeReply(SendResult.SWITCHED, session=name)

    async def async_list(self, echo: str | None) -> BridgeReply:
        """Return the running sessions and the active one."""
        if (refused := self._check(echo)) is not None:
            return BridgeReply(refused)
        status, data = await self._async_request("GET", "/sessions")
        if status != 200:
            return BridgeReply(SendResult.UNREACHABLE)
        return BridgeReply(
            SendResult.LISTED,
            sessions=list(data.get("sessions") or []),
            active=str(data.get("active") or MAIN_SESSION),
        )

    async def async_end(self, spoken: str, echo: str | None) -> BridgeReply:
        """End a voice session; the main session stays."""
        if (refused := self._check(echo)) is not None:
            return BridgeReply(refused)
        name = session_name(spoken)
        if not name:
            return BridgeReply(SendResult.NO_NAME)
        if name == MAIN_SESSION:
            return BridgeReply(SendResult.MAIN_SESSION, session=name)
        status, data = await self._async_request("POST", "/end", {"name": name})
        if status == 404:
            return BridgeReply(
                SendResult.UNKNOWN_SESSION,
                session=name,
                sessions=list(data.get("sessions") or []),
            )
        if status != 200:
            return BridgeReply(SendResult.UNREACHABLE)
        self._pending.pop(name, None)
        return BridgeReply(SendResult.ENDED, session=name)

    async def _async_handle_answer(
        self, hass: HomeAssistant, webhook_id: str, request: web.Request
    ) -> web.Response:
        """Speak Claude's answer on the Echo that asked."""
        try:
            payload = await request.json()
        except ValueError:
            return web.Response(status=400)
        text = payload.get("text") if isinstance(payload, dict) else None
        if not isinstance(text, str) or not text.strip():
            return web.Response(status=400)

        session = payload.get("session")
        session = session if isinstance(session, str) and session else MAIN_SESSION
        pending = self._pending.pop(session, None)
        if pending is None or time.monotonic() - pending.sent > PENDING_SECONDS:
            # Nobody asked this session by voice (or too long ago): keep quiet
            return web.json_response({"spoken": False})

        text = text.strip()[:MAX_ANSWER_LENGTH]
        speech = spoken_part(text) or "Claude ist fertig."
        if session != MAIN_SESSION:
            speech = f"{session}: {speech}"
        has_more = len(" ".join(text.split())) > len(speech) + 20
        if has_more:
            speech = f"{speech} {CLAUDE_REST_TEXT}"
        await self.hass.services.async_call(
            "notify",
            "alexa_media",
            {
                "target": [pending.echo],
                "data": {"type": "announce"},
                "message": speech,
            },
            blocking=False,
        )
        if has_more:
            await self.manager.async_send_to_mobile(
                question=f"Claude {session}: {pending.prompt}",
                answer=text,
                reply_device=pending.echo,
                confirm=False,
            )
        self.manager.add_history_entry(
            pending.echo,
            f"[Claude {session}] {pending.prompt}",
            speech,
            duration=time.monotonic() - pending.sent,
            char_count=len(text),
            mode="Claude",
        )
        return web.json_response({"spoken": True})
