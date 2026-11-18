#!/usr/bin/env python3
"""Claude bridge for Schlaue Antworten.

Home Assistant posts spoken prompts and session commands here:

- POST /prompt    {text, reply_url}        type into the active session
- POST /sessions  {name, text?, reply_url?} start a voice session (and switch)
- POST /switch    {name}                    send following prompts there
- POST /end       {name}                    end a voice session
- GET  /sessions                            running sessions and the active one
- GET  /health

The main session "alexa" runs on tmux socket "alexa" (claude-alexa-session
.service). Voice sessions run on socket "alexa-x", one tmux session each, and
end after some idle time. The Stop hook of each session (stop_hook.py) posts
its answer back, using the pending file named after the Claude session id.

Only the standard library is used, so it runs with the system Python.
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import threading
import time
from urllib.parse import urlparse
import uuid

HOME = Path.home()
TOKEN_FILE = Path(
    os.environ.get("CLAUDE_ALEXA_TOKEN_FILE", HOME / ".config/claude-alexa/token")
)
STATE_DIR = Path(os.environ.get("CLAUDE_ALEXA_STATE", HOME / "claude-alexa/state"))
PENDING_DIR = STATE_DIR / "pending"
SESSIONS_FILE = STATE_DIR / "sessions.json"
MAIN_ID_FILE = STATE_DIR / "session_id"
VOICE_SCRIPT = HOME / "claude-alexa/run_voice_session.sh"
MAIN_SESSION = os.environ.get("CLAUDE_ALEXA_TMUX", "alexa")
MAIN_SOCKET = os.environ.get("CLAUDE_ALEXA_TMUX_SOCKET", "alexa")
VOICE_SOCKET = os.environ.get("CLAUDE_ALEXA_VOICE_SOCKET", "alexa-x")
BIND = os.environ.get("CLAUDE_ALEXA_BIND", "0.0.0.0")
PORT = int(os.environ.get("CLAUDE_ALEXA_PORT", "8765"))
MAX_VOICE_SESSIONS = int(os.environ.get("CLAUDE_ALEXA_MAX_SESSIONS", "3"))
IDLE_SECONDS = int(os.environ.get("CLAUDE_ALEXA_IDLE_SECONDS", str(2 * 3600)))
# Home Assistant's address (set by install.sh in ~/.config/claude-alexa/env)
# and this machine; nobody else may send prompts
ALLOWED_HOSTS = {
    host.strip()
    for host in os.environ.get("CLAUDE_ALEXA_ALLOWED", "127.0.0.1").split(",")
    if host.strip()
}
MAX_TEXT = 600
MAX_BODY = 8192
ENTER_ATTEMPTS = 4
READY_SECONDS = 60
RE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,19}$")

_LOGGER = logging.getLogger("claude-alexa-bridge")
_LOCK = threading.Lock()


def clean_text(text: str) -> str:
    """Return one line of printable text, so tmux types nothing unexpected."""
    printable = "".join(ch if ch.isprintable() else " " for ch in text)
    return " ".join(printable.split())[:MAX_TEXT]


def tmux(socket: str, *args: str, check: bool = False) -> subprocess.CompletedProcess:
    """Run tmux on one of the bridge's sockets."""
    return subprocess.run(
        ["tmux", "-L", socket, *args], capture_output=True, text=True, check=check
    )


def socket_of(name: str) -> str:
    """Return the tmux socket a session runs on."""
    return MAIN_SOCKET if name == MAIN_SESSION else VOICE_SOCKET


def running(name: str) -> bool:
    """Return whether the tmux session of a Claude session exists."""
    return tmux(socket_of(name), "has-session", "-t", f"={name}").returncode == 0


def _pane(name: str) -> str:
    return tmux(socket_of(name), "capture-pane", "-p", "-t", f"={name}:").stdout


def _input_lines(name: str) -> list[str]:
    return [line for line in _pane(name).splitlines() if line.lstrip().startswith("❯")]


def sent_count(name: str, text: str) -> int:
    """Return how often the prompt shows in the history (above the input)."""
    head = text[:30]
    return sum(head in line for line in _input_lines(name)[:-1])


def prompt_state(name: str, text: str, sent_before: int) -> str:
    """Return where the prompt is: "sent", "input" (unsent) or "lost".

    After sending, the prompt shows up once more in the history and an empty
    input line follows; while unsent, the last input line still holds its
    beginning. Typed right after a start, it can also vanish completely.
    """
    head = text[:30]
    lines = _input_lines(name)
    if lines and head in lines[-1]:
        return "input"
    if sum(head in line for line in lines[:-1]) > sent_before:
        return "sent"
    return "lost"


def wait_ready(name: str) -> bool:
    """Wait until Claude's input box is shown (after a start)."""
    deadline = time.time() + READY_SECONDS
    while time.time() < deadline:
        pane = _pane(name)
        if "auto mode" in pane or "bypass" in pane.lower():
            # The status line comes slightly before the input box takes keys
            time.sleep(2)
            return True
        time.sleep(1)
    return False


def close_dialogs(name: str) -> None:
    """Close a question Claude shows (e.g. hints after a start) with Esc.

    Typed text would otherwise go into the dialog and might pick an option.
    The folder trust question is left alone: Esc would end the session.
    """
    socket, target = socket_of(name), f"={name}:"
    for _attempt in range(3):
        pane = _pane(name)
        if "Enter to confirm" not in pane or "trust" in pane.lower():
            return
        _LOGGER.info("Closing a dialog in session %s", name)
        tmux(socket, "send-keys", "-t", target, "Escape")
        time.sleep(1.0)


def type_prompt(name: str, text: str) -> None:
    """Type the prompt into a Claude session and press Enter.

    Right after a (re)start the input box may swallow Enter, so it is pressed
    again while the prompt still sits there.
    """
    socket, target = socket_of(name), f"={name}:"
    close_dialogs(name)
    sent_before = sent_count(name, text)
    for _attempt in range(ENTER_ATTEMPTS):
        state = prompt_state(name, text, sent_before)
        if state == "lost":
            tmux(socket, "send-keys", "-t", target, "-l", text, check=True)
        # Give the input box a moment, otherwise Enter can arrive before the text
        time.sleep(0.5)
        tmux(socket, "send-keys", "-t", target, "Enter", check=True)
        time.sleep(1.5)
        if prompt_state(name, text, sent_before) == "sent":
            return
    _LOGGER.warning("The prompt may not have reached session %s", name)


def load_state() -> dict:
    """Return active session and voice sessions {name: {id, last}}."""
    try:
        state = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    state.setdefault("active", MAIN_SESSION)
    state.setdefault("sessions", {})
    return state


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = SESSIONS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state), encoding="utf-8")
    tmp.replace(SESSIONS_FILE)


def prune(state: dict) -> None:
    """Forget voice sessions whose tmux session is gone."""
    for name in list(state["sessions"]):
        if not running(name):
            del state["sessions"][name]
    if state["active"] != MAIN_SESSION and state["active"] not in state["sessions"]:
        state["active"] = MAIN_SESSION


def session_names(state: dict) -> list[str]:
    return [MAIN_SESSION, *sorted(state["sessions"])]


def claude_id(state: dict, name: str) -> str:
    """Return the Claude session id of a session."""
    if name == MAIN_SESSION:
        return MAIN_ID_FILE.read_text(encoding="utf-8").strip()
    return state["sessions"][name]["id"]


def write_pending(session_id: str, name: str, reply_url: str, text: str) -> None:
    """Remember where the next answer of a session goes (for stop_hook.py)."""
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(PENDING_DIR, 0o700)
    target = PENDING_DIR / f"{session_id}.json"
    tmp = target.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(
            {"reply_url": reply_url, "session": name, "prompt": text, "time": time.time()}
        ),
        encoding="utf-8",
    )
    tmp.replace(target)


def deliver(name: str, session_id: str, text: str, reply_url: str) -> bool:
    """Note the reply address and type the prompt; False if tmux failed."""
    write_pending(session_id, name, reply_url, text)
    try:
        type_prompt(name, text)
    except subprocess.CalledProcessError as err:
        _LOGGER.error("tmux failed for %s: %s", name, err)
        (PENDING_DIR / f"{session_id}.json").unlink(missing_ok=True)
        return False
    return True


def start_voice_session(name: str, session_id: str, text: str, reply_url: str) -> None:
    """Start a voice session and type its first prompt once it is ready."""
    result = tmux(
        VOICE_SOCKET,
        "new-session", "-d", "-s", name, "-x", "220", "-y", "50",
        f"{VOICE_SCRIPT} {name} {session_id}",
    )
    if result.returncode != 0:
        _LOGGER.error("Could not start session %s: %s", name, result.stderr.strip())
        return
    if not wait_ready(name):
        _LOGGER.warning("Session %s did not get ready in time", name)
        return
    _LOGGER.info("Voice session %s started", name)
    if text:
        deliver(name, session_id, text, reply_url)


def end_voice_session(name: str) -> None:
    tmux(VOICE_SOCKET, "kill-session", "-t", f"={name}")


def idle_reaper() -> None:
    """End voice sessions nobody sent a prompt to for a long time."""
    while True:
        time.sleep(300)
        with _LOCK:
            state = load_state()
            now = time.time()
            for name, info in list(state["sessions"].items()):
                if now - float(info.get("last", now)) > IDLE_SECONDS:
                    _LOGGER.info("Ending idle voice session %s", name)
                    end_voice_session(name)
            prune(state)
            save_state(state)


class Handler(BaseHTTPRequestHandler):
    """Serve the bridge API."""

    server_version = "ClaudeAlexaBridge/2"

    def _reply(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _allowed(self) -> bool:
        return self.client_address[0] in ALLOWED_HOSTS

    def _authorized(self) -> bool:
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
        given = self.headers.get("Authorization", "")
        return bool(token) and hmac.compare_digest(given, f"Bearer {token}")

    def _gate(self) -> bool:
        """Reply with an error and return False unless the caller may talk."""
        if not self._allowed():
            self._reply(403, {"error": "forbidden"})
            return False
        if self.path != "/health" and not self._authorized():
            _LOGGER.warning("Rejected a request with a wrong token")
            self._reply(401, {"error": "unauthorized"})
            return False
        return True

    def _body(self) -> dict | None:
        length = int(self.headers.get("Content-Length") or 0)
        if not 0 < length <= MAX_BODY:
            return None
        try:
            payload = json.loads(self.rfile.read(length))
        except ValueError:
            return None
        return payload if isinstance(payload, dict) else None

    @staticmethod
    def _prompt_of(payload: dict) -> tuple[str, str] | None:
        """Return text and reply address, or None if they are not valid."""
        text = clean_text(str(payload.get("text") or ""))
        reply_url = str(payload.get("reply_url") or "")
        parsed = urlparse(reply_url)
        # The answer only ever goes back to Home Assistant itself
        if (
            len(text) < 2
            or parsed.scheme not in ("http", "https")
            or parsed.hostname not in ALLOWED_HOSTS
        ):
            return None
        return text, reply_url

    def do_GET(self) -> None:  # noqa: N802
        if not self._gate():
            return
        if self.path == "/health":
            self._reply(200, {"session": running(MAIN_SESSION)})
        elif self.path == "/sessions":
            with _LOCK:
                state = load_state()
                prune(state)
                save_state(state)
            self._reply(
                200, {"sessions": session_names(state), "active": state["active"]}
            )
        else:
            self._reply(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if not self._gate():
            return
        handlers = {
            "/prompt": self._prompt,
            "/sessions": self._new_session,
            "/switch": self._switch,
            "/end": self._end,
        }
        handler = handlers.get(self.path)
        if handler is None:
            self._reply(404, {"error": "not found"})
            return
        payload = self._body()
        if payload is None:
            self._reply(400, {"error": "bad request"})
            return
        handler(payload)

    def _prompt(self, payload: dict) -> None:
        prompt = self._prompt_of(payload)
        if prompt is None:
            self._reply(400, {"error": "bad prompt"})
            return
        with _LOCK:
            state = load_state()
            prune(state)
            name = state["active"]
            if name != MAIN_SESSION:
                state["sessions"][name]["last"] = time.time()
            save_state(state)
            session_id = claude_id(state, name)
        if not running(name):
            self._reply(503, {"error": "claude session not running"})
            return
        if not deliver(name, session_id, *prompt):
            self._reply(503, {"error": "tmux failed"})
            return
        _LOGGER.info("Prompt typed into session %s (%d chars)", name, len(prompt[0]))
        self._reply(200, {"ok": True, "session": name})

    def _new_session(self, payload: dict) -> None:
        name = str(payload.get("name") or "")
        if not RE_NAME.match(name) or name == MAIN_SESSION:
            self._reply(400, {"error": "bad name"})
            return
        prompt = self._prompt_of(payload) if payload.get("text") else ("", "")
        if prompt is None:
            self._reply(400, {"error": "bad prompt"})
            return
        with _LOCK:
            state = load_state()
            prune(state)
            if name in state["sessions"]:
                # Exists already: switch to it and hand over the prompt
                state["active"] = name
                state["sessions"][name]["last"] = time.time()
                save_state(state)
                if prompt[0]:
                    deliver(name, state["sessions"][name]["id"], *prompt)
                self._reply(200, {"session": name, "existed": True})
                return
            if len(state["sessions"]) >= MAX_VOICE_SESSIONS:
                self._reply(409, {"sessions": session_names(state)})
                return
            session_id = str(uuid.uuid4())
            state["sessions"][name] = {"id": session_id, "last": time.time()}
            state["active"] = name
            save_state(state)
        # Starting Claude takes a while; Home Assistant gets its answer now
        threading.Thread(
            target=start_voice_session,
            args=(name, session_id, *prompt),
            daemon=True,
        ).start()
        self._reply(200, {"session": name})

    def _switch(self, payload: dict) -> None:
        name = str(payload.get("name") or "")
        with _LOCK:
            state = load_state()
            prune(state)
            if name != MAIN_SESSION and name not in state["sessions"]:
                self._reply(404, {"sessions": session_names(state)})
                return
            state["active"] = name
            save_state(state)
        self._reply(200, {"active": name})

    def _end(self, payload: dict) -> None:
        name = str(payload.get("name") or "")
        with _LOCK:
            state = load_state()
            prune(state)
            if name == MAIN_SESSION or name not in state["sessions"]:
                self._reply(404, {"sessions": session_names(state)})
                return
            end_voice_session(name)
            del state["sessions"][name]
            if state["active"] == name:
                state["active"] = MAIN_SESSION
            save_state(state)
        _LOGGER.info("Voice session %s ended", name)
        self._reply(200, {"ok": True, "active": state["active"]})

    def log_message(self, fmt: str, *args: object) -> None:
        _LOGGER.debug("%s %s", self.client_address[0], fmt % args)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if not TOKEN_FILE.exists():
        raise SystemExit(f"Token file missing: {TOKEN_FILE}")
    threading.Thread(target=idle_reaper, daemon=True).start()
    server = ThreadingHTTPServer((BIND, PORT), Handler)
    _LOGGER.info("Listening on %s:%s", BIND, PORT)
    server.serve_forever()


if __name__ == "__main__":
    main()
