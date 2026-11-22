"""Tests for the transcript history of the Ubuntu-side Claude bridge."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType

import pytest

BRIDGE_FILE = Path(__file__).parent.parent / "tools" / "claude_bridge" / "bridge.py"
SESSION = "12345678-1234-1234-1234-123456789abc"


@pytest.fixture
def bridge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Load bridge.py with its Claude folder in a temporary directory."""
    spec = importlib.util.spec_from_file_location("claude_bridge_tool", BRIDGE_FILE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "CLAUDE_PROJECTS_DIR", tmp_path)
    return module


def _write(tmp_path: Path, entries: list[dict]) -> None:
    folder = tmp_path / "-mnt-ha-config"
    folder.mkdir()
    (folder / f"{SESSION}.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8"
    )


def test_history_keeps_only_what_was_said(bridge: ModuleType, tmp_path: Path) -> None:
    """Tool calls, meta entries and reminders are left out; blocks merge."""
    _write(
        tmp_path,
        [
            {"type": "user", "timestamp": "t1", "message": {"content": (
                "[Alexa · Küche] Licht an<system-reminder>geheim</system-reminder>")}},
            {"type": "user", "isMeta": True, "message": {"content": "meta"}},
            {"type": "user", "message": {"content": "<command-name>/clear</command-name>"}},
            {"type": "assistant", "timestamp": "t2", "message": {"id": "m1", "content": [
                {"type": "text", "text": "Mache ich."},
                {"type": "tool_use", "name": "Bash", "input": {}}]}},
            {"type": "user", "message": {"content": [
                {"type": "tool_result", "content": "ok"}]}},
            {"type": "assistant", "timestamp": "t3", "message": {"id": "m1", "content": [
                {"type": "text", "text": "Licht ist an."}]}},
            {"type": "summary", "summary": "x"},
        ],
    )
    history = bridge.session_history(SESSION, 60)
    assert history == [
        {"role": "user", "text": "[Alexa · Küche] Licht an", "time": "t1"},
        {"role": "assistant", "text": "Mache ich.\n\nLicht ist an.", "time": "t2"},
    ]
    assert bridge.session_history(SESSION, 1) == history[-1:]


def test_history_rejects_unknown_or_bad_ids(bridge: ModuleType, tmp_path: Path) -> None:
    """Only real session ids are looked up; path tricks find nothing."""
    assert bridge.session_history("../../etc/passwd", 10) is None
    assert bridge.session_history(SESSION, 10) is None
