#!/usr/bin/env python3
"""Claude bridge for Schlaue Antworten.

Home Assistant posts a spoken prompt to POST /prompt. The bridge types it into
the Claude Code session running in tmux and notes where the answer must go.
The Stop hook of that session (stop_hook.py) posts the answer back.

Only the standard library is used, so it runs with the system Python.
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import logging
import os
from pathlib import Path
import subprocess
import time
from urllib.parse import urlparse

HOME = Path.home()
TOKEN_FILE = Path(
    os.environ.get("CLAUDE_ALEXA_TOKEN_FILE", HOME / ".config/claude-alexa/token")
)
STATE_DIR = Path(os.environ.get("CLAUDE_ALEXA_STATE", HOME / "claude-alexa/state"))
PENDING_FILE = STATE_DIR / "pending.json"
TMUX_SESSION = os.environ.get("CLAUDE_ALEXA_TMUX", "alexa")
BIND = os.environ.get("CLAUDE_ALEXA_BIND", "0.0.0.0")
PORT = int(os.environ.get("CLAUDE_ALEXA_PORT", "8765"))
# Home Assistant's address (set by install.sh in ~/.config/claude-alexa/env)
# and this machine; nobody else may send prompts
ALLOWED_HOSTS = {
    host.strip()
    for host in os.environ.get("CLAUDE_ALEXA_ALLOWED", "127.0.0.1").split(",")
    if host.strip()
}
MAX_TEXT = 600
MAX_BODY = 8192

_LOGGER = logging.getLogger("claude-alexa-bridge")


def clean_text(text: str) -> str:
    """Return one line of printable text, so tmux types nothing unexpected."""
    printable = "".join(ch if ch.isprintable() else " " for ch in text)
    return " ".join(printable.split())[:MAX_TEXT]


def session_running() -> bool:
    """Return whether the tmux session with Claude exists."""
    return (
        subprocess.run(
            ["tmux", "has-session", "-t", f"={TMUX_SESSION}"],
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


def type_prompt(text: str) -> None:
    """Type the prompt into the Claude session and press Enter."""
    target = f"={TMUX_SESSION}:"
    subprocess.run(["tmux", "send-keys", "-t", target, "-l", text], check=True)
    # Give the input box a moment, otherwise Enter can arrive before the text
    time.sleep(0.3)
    subprocess.run(["tmux", "send-keys", "-t", target, "Enter"], check=True)


def write_pending(reply_url: str, text: str) -> None:
    """Remember where the next answer goes (read by stop_hook.py)."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = PENDING_FILE.with_suffix(".tmp")
    tmp.write_text(
        json.dumps({"reply_url": reply_url, "prompt": text, "time": time.time()}),
        encoding="utf-8",
    )
    os.chmod(tmp, 0o600)
    tmp.replace(PENDING_FILE)


class Handler(BaseHTTPRequestHandler):
    """Serve /prompt and /health."""

    server_version = "ClaudeAlexaBridge/1"

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

    def do_GET(self) -> None:  # noqa: N802
        if not self._allowed():
            self._reply(403, {"error": "forbidden"})
        elif self.path == "/health":
            self._reply(200, {"session": session_running()})
        else:
            self._reply(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if not self._allowed():
            self._reply(403, {"error": "forbidden"})
            return
        if self.path != "/prompt":
            self._reply(404, {"error": "not found"})
            return
        if not self._authorized():
            _LOGGER.warning("Rejected a prompt with a wrong token")
            self._reply(401, {"error": "unauthorized"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if not 0 < length <= MAX_BODY:
            self._reply(400, {"error": "bad length"})
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except ValueError:
            self._reply(400, {"error": "bad json"})
            return
        text = clean_text(str(payload.get("text") or ""))
        reply_url = str(payload.get("reply_url") or "")
        parsed = urlparse(reply_url)
        if len(text) < 2 or parsed.scheme not in ("http", "https"):
            self._reply(400, {"error": "bad prompt"})
            return
        # The answer only ever goes back to Home Assistant itself
        if parsed.hostname not in ALLOWED_HOSTS:
            self._reply(400, {"error": "bad reply_url"})
            return
        if not session_running():
            self._reply(503, {"error": "claude session not running"})
            return
        write_pending(reply_url, text)
        try:
            type_prompt(text)
        except subprocess.CalledProcessError as err:
            _LOGGER.error("tmux failed: %s", err)
            PENDING_FILE.unlink(missing_ok=True)
            self._reply(503, {"error": "tmux failed"})
            return
        _LOGGER.info("Prompt typed into the Claude session (%d chars)", len(text))
        self._reply(200, {"ok": True})

    def log_message(self, fmt: str, *args: object) -> None:
        _LOGGER.debug("%s %s", self.client_address[0], fmt % args)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if not TOKEN_FILE.exists():
        raise SystemExit(f"Token file missing: {TOKEN_FILE}")
    server = ThreadingHTTPServer((BIND, PORT), Handler)
    _LOGGER.info("Listening on %s:%s, tmux session %r", BIND, PORT, TMUX_SESSION)
    server.serve_forever()


if __name__ == "__main__":
    main()
