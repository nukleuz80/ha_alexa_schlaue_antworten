#!/usr/bin/env python3
"""Stop hook of the Claude sessions started for Alexa.

When Claude has finished a turn that started with a voice prompt
("[Alexa · ...] ..."), the answer is posted back to Home Assistant, which
speaks it on the Echo that asked. A turn started from the chat panel of
Home Assistant ("[HA-Chat] ...") goes back to the chat, with the prompt id
and reply token the bridge noted. Any other turn is left alone.
The hook never blocks Claude: every problem ends in exit code 0.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.request

STATE_DIR = Path(
    os.environ.get("CLAUDE_ALEXA_STATE", Path.home() / "claude-alexa/state")
)
PENDING_DIR = STATE_DIR / "pending"
PENDING_SECONDS = 30 * 60
PREFIX = "[Alexa"
CHAT_PREFIX = "[HA-Chat]"
# Long typed prompts are stored as a paste: <pasted_content id="..."> ... text
RE_PASTE_START = re.compile(r"^\s*<pasted_content[^>]*>\s*")


def _text_of(content: object) -> str:
    """Return the text blocks of a message content."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


def last_turn(transcript: Path) -> tuple[str, str]:
    """Return the last typed user prompt and Claude's last text after it."""
    prompt, answer = "", ""
    with transcript.open(encoding="utf-8") as lines:
        for line in lines:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get("isSidechain"):
                continue
            message = entry.get("message") or {}
            content = message.get("content")
            if entry.get("type") == "user":
                text = _text_of(content)
                # Tool results come as user entries too; they carry no text block
                if text.strip():
                    prompt, answer = text.strip(), ""
            elif entry.get("type") == "assistant":
                text = _text_of(content)
                if text.strip():
                    answer = text.strip()
    return prompt, answer


def main() -> None:
    try:
        hook = json.load(sys.stdin)
    except ValueError:
        return
    # Each session has its own pending file, named after its Claude session id
    session_id = str(hook.get("session_id") or "")
    if not session_id or "/" in session_id:
        return
    if not any(
        (PENDING_DIR / name).exists()
        for name in (f"{session_id}.json", f"{session_id}.chat.json")
    ):
        return  # nothing from outside waits for an answer
    prompt, answer = "", ""
    transcript = hook.get("transcript_path")
    if transcript and Path(transcript).exists():
        prompt, answer = last_turn(Path(transcript))
    prompt = RE_PASTE_START.sub("", prompt)
    if prompt.startswith(CHAT_PREFIX):
        pending_file = PENDING_DIR / f"{session_id}.chat.json"
    elif prompt.startswith(PREFIX):
        pending_file = PENDING_DIR / f"{session_id}.json"
    else:
        # This turn was typed in the app; a prompt from outside may be queued
        return
    if not pending_file.exists():
        return
    try:
        pending = json.loads(pending_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pending_file.unlink(missing_ok=True)
        return
    if time.time() - float(pending.get("time", 0)) > PENDING_SECONDS:
        pending_file.unlink(missing_ok=True)
        return
    answer = str(hook.get("last_assistant_message") or "").strip() or answer
    if not answer:
        return

    pending_file.unlink(missing_ok=True)
    body = {"text": answer, "session": pending.get("session") or "alexa"}
    extra = pending.get("reply_extra")
    if isinstance(extra, dict):
        body.update({str(key): str(value) for key, value in extra.items()})
    request = urllib.request.Request(
        pending["reply_url"],
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8):
            pass
    except OSError as err:
        print(f"Antwort an Home Assistant fehlgeschlagen: {err}", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # noqa: BLE001 - never break the Claude session
        print(f"Alexa-Stop-Hook: {err}", file=sys.stderr)
    sys.exit(0)
