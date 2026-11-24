#!/usr/bin/env python3
"""PermissionRequest hook of the bridge sessions: ask on the phone.

When Claude Code is about to ask for permission, the request goes to the
bridge, Home Assistant shows it as a push with "Erlauben" / "Ablehnen", and
the answer comes back here. Without an answer in time (or if the bridge is
not reachable) the hook prints nothing, and Claude Code shows its normal
permission prompt (terminal / Claude app). It never blocks on its own.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

BRIDGE = os.environ.get(
    "CLAUDE_ALEXA_BRIDGE",
    f"http://127.0.0.1:{os.environ.get('CLAUDE_ALEXA_PORT', '8765')}",
)
TOKEN_FILE = Path(
    os.environ.get(
        "CLAUDE_ALEXA_TOKEN_FILE", Path.home() / ".config/claude-alexa/token"
    )
)
# How long to wait for an answer before the normal prompt takes over
WAIT_SECONDS = float(os.environ.get("CLAUDE_ALEXA_APPROVAL_WAIT", "120"))
POLL_SECONDS = 25


def _call(method: str, path: str, payload: dict | None, timeout: float) -> dict:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    request = urllib.request.Request(
        BRIDGE + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read() or b"{}")
    return data if isinstance(data, dict) else {}


def decision_output(decision: dict) -> dict:
    """The hook answer Claude Code expects for a decision of the bridge."""
    result: dict = {"behavior": decision.get("behavior")}
    if result["behavior"] == "deny":
        result["message"] = decision.get("message") or "Am Handy abgelehnt."
    return {
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": result,
        }
    }


def ask(event: dict, wait: float = WAIT_SECONDS) -> dict | None:
    """Post the request and wait for the answer; None = no answer."""
    created = _call(
        "POST",
        "/approval",
        {
            "session_id": event.get("session_id"),
            "tool_name": event.get("tool_name"),
            "tool_input": event.get("tool_input"),
            "cwd": event.get("cwd"),
        },
        10,
    )
    key = str(created.get("id") or "")
    if not key:
        return None
    deadline = time.time() + wait
    try:
        while (left := deadline - time.time()) > 0:
            step = min(POLL_SECONDS, left)
            answer = _call("GET", f"/approval?id={key}&wait={step:.0f}", None, step + 10)
            decision = answer.get("decision")
            if isinstance(decision, dict) and decision.get("behavior") in ("allow", "deny"):
                return decision
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return None
        raise
    _call("POST", "/approval/cancel", {"id": key}, 10)
    return None


def main() -> None:
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict) or event.get("hook_event_name") != "PermissionRequest":
            return
        decision = ask(event)
    except (OSError, ValueError) as err:
        print(f"permission_hook: {err}", file=sys.stderr)
        return
    if decision:
        print(json.dumps(decision_output(decision)))


if __name__ == "__main__":
    main()
    sys.exit(0)
