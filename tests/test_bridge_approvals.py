"""Tests for permission requests (approvals) through the Claude bridge."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import threading
import time
from types import ModuleType

import pytest

TOOL_DIR = Path(__file__).parent.parent / "tools" / "claude_bridge"
SID = "12345678-1234-1234-1234-123456789abc"


def _load(name: str, file: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, TOOL_DIR / file)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def bridge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    module = _load("claude_bridge_approvals", "bridge.py")
    (tmp_path / "session_id").write_text(SID, encoding="utf-8")
    monkeypatch.setattr(module, "MAIN_ID_FILE", tmp_path / "session_id")
    monkeypatch.setattr(module, "AGENTS_FILE", tmp_path / "none.json")
    module._APPROVALS.clear()
    return module


def _add(bridge: ModuleType, **extra: object) -> str:
    key = bridge.approval_add({
        "session_id": SID, "tool_name": "Bash",
        "tool_input": {"command": "ha core restart", "description": "x"}, **extra,
    })
    assert key
    return key


def test_add_lists_open_with_session_name(bridge: ModuleType) -> None:
    key = _add(bridge)
    items = bridge.approvals_open({"active": "alexa", "sessions": {}})
    assert items == [{
        "id": key, "session_id": SID, "session": "alexa", "tool": "Bash",
        "summary": "ha core restart", "created": items[0]["created"],
    }]


def test_add_rejects_bad_input(bridge: ModuleType) -> None:
    assert bridge.approval_add({"session_id": "x", "tool_name": "Bash"}) is None
    assert bridge.approval_add({"session_id": SID, "tool_name": ""}) is None


def test_limit(bridge: ModuleType) -> None:
    for _ in range(bridge.APPROVAL_MAX):
        _add(bridge)
    assert bridge.approval_add({"session_id": SID, "tool_name": "Bash"}) is None


def test_decide_wakes_waiter_once(bridge: ModuleType) -> None:
    key = _add(bridge)
    result: list[object] = []
    waiter = threading.Thread(target=lambda: result.append(bridge.approval_wait(key, 5)))
    waiter.start()
    time.sleep(0.1)
    assert bridge.approval_decide(key, "deny", "nein")
    assert not bridge.approval_decide(key, "allow")  # answered already
    waiter.join(3)
    assert result == [{"behavior": "deny", "message": "nein"}]
    assert bridge.approvals_open({"active": "alexa", "sessions": {}}) == []
    bridge.approvals_prune()
    with pytest.raises(KeyError):
        bridge.approval_wait(key, 0)


def test_wait_times_out_and_cancel(bridge: ModuleType) -> None:
    key = _add(bridge)
    assert bridge.approval_wait(key, 0.05) is None
    assert not bridge.approval_decide(key, "vielleicht")
    bridge.approval_cancel(key)
    assert not bridge.approval_decide(key, "allow")


def test_old_requests_expire(bridge: ModuleType) -> None:
    key = _add(bridge)
    bridge._APPROVALS[key]["created"] -= bridge.APPROVAL_TTL + 1
    assert bridge.approvals_open({"active": "alexa", "sessions": {}}) == []


def test_summary_fallbacks(bridge: ModuleType) -> None:
    assert bridge._summary("Edit", {"file_path": "/a/b.py", "old_string": "x"}) == "/a/b.py"
    assert bridge._summary("mcp__x", {"a": 1}) == '{"a": 1}'
    assert bridge._summary("x", None) == ""


def test_hook_output_and_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    hook = _load("permission_hook_test", "permission_hook.py")
    assert hook.decision_output({"behavior": "allow"}) == {
        "hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": {"behavior": "allow"}}
    }
    deny = hook.decision_output({"behavior": "deny", "message": ""})
    assert deny["hookSpecificOutput"]["decision"]["message"] == "Am Handy abgelehnt."

    calls: list[tuple[str, str]] = []
    answers = iter([{"id": "a" * 32}, {"decision": None}, {"decision": {"behavior": "allow"}}])

    def fake_call(method: str, path: str, payload: object, timeout: float) -> dict:
        calls.append((method, path.split("?")[0]))
        return next(answers)

    monkeypatch.setattr(hook, "_call", fake_call)
    assert hook.ask({"session_id": SID, "tool_name": "Bash"}, wait=60) == {"behavior": "allow"}
    assert calls == [("POST", "/approval"), ("GET", "/approval"), ("GET", "/approval")]


def test_hook_gives_up_and_cancels(monkeypatch: pytest.MonkeyPatch) -> None:
    hook = _load("permission_hook_test2", "permission_hook.py")
    calls: list[str] = []

    def fake_call(method: str, path: str, payload: object, timeout: float) -> dict:
        calls.append(path.split("?")[0])
        return {"id": "b" * 32} if path == "/approval" and method == "POST" else {}

    monkeypatch.setattr(hook, "_call", fake_call)
    assert hook.ask({"session_id": SID, "tool_name": "Bash"}, wait=0) is None
    assert calls == ["/approval", "/approval/cancel"]


def test_hook_main_silent_without_bridge(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    hook = _load("permission_hook_test3", "permission_hook.py")
    monkeypatch.setattr(hook, "BRIDGE", "http://127.0.0.1:1")
    monkeypatch.setattr(hook, "TOKEN_FILE", Path("/nonexistent/token"))
    monkeypatch.setattr(sys, "stdin", __import__("io").StringIO(json.dumps(
        {"hook_event_name": "PermissionRequest", "session_id": SID, "tool_name": "Bash"})))
    hook.main()
    out = capsys.readouterr()
    assert out.out == "" and "permission_hook" in out.err
