"""Tests for the fixed agents of the Ubuntu-side Claude bridge."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType

import pytest

TOOL_DIR = Path(__file__).parent.parent / "tools" / "claude_bridge"
BRIDGE_FILE = TOOL_DIR / "bridge.py"


@pytest.fixture
def bridge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Load bridge.py with agents.json and state in a temporary directory."""
    spec = importlib.util.spec_from_file_location("claude_bridge_agents", BRIDGE_FILE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    agents = tmp_path / "agents.json"
    agents.write_text(json.dumps({"agents": [
        {"name": "brainstorm"}, {"name": "analyse", "model": "sonnet"},
        {"name": "alexa"}, {"name": "Böse Name"}, {"name": "brainstorm"},
    ]}), encoding="utf-8")
    monkeypatch.setattr(module, "AGENTS_FILE", agents)
    monkeypatch.setattr(module, "AGENT_STATE_DIR", tmp_path / "agents")
    monkeypatch.setattr(module, "MAIN_ID_FILE", tmp_path / "session_id")
    return module


def test_fixed_agents_are_valid_and_unique(bridge: ModuleType) -> None:
    """Bad names, duplicates and the main session are left out."""
    assert bridge.fixed_agents() == ["brainstorm", "analyse"]


def test_missing_agents_file_means_none(
    bridge: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bridge, "AGENTS_FILE", tmp_path / "fehlt.json")
    assert bridge.fixed_agents() == []
    (tmp_path / "kaputt.json").write_text("{", encoding="utf-8")
    monkeypatch.setattr(bridge, "AGENTS_FILE", tmp_path / "kaputt.json")
    assert bridge.fixed_agents() == []


def test_each_agent_has_its_own_socket(bridge: ModuleType) -> None:
    assert bridge.socket_of("alexa") == bridge.MAIN_SOCKET
    assert bridge.socket_of("brainstorm") == "agent-brainstorm"
    assert bridge.socket_of("einkauf") == bridge.VOICE_SOCKET


def test_agents_are_known_and_listed(bridge: ModuleType, tmp_path: Path) -> None:
    """Agents come right after alexa; their id comes from the state folder."""
    state = {"active": "alexa", "sessions": {"zz": {"id": "x"}}}
    assert bridge.session_names(state) == ["alexa", "brainstorm", "analyse", "zz"]
    assert bridge.known(state, "analyse")
    assert not bridge.known(state, "fremd")
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "analyse.id").write_text("abc\n", encoding="utf-8")
    assert bridge.claude_id(state, "analyse") == "abc"


def test_prune_keeps_a_switch_to_an_agent(
    bridge: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bridge, "running", lambda name: False)
    state = {"active": "brainstorm", "sessions": {}}
    bridge.prune(state)
    assert state["active"] == "brainstorm"
    state["active"] = "weg"
    bridge.prune(state)
    assert state["active"] == "alexa"


def test_shipped_agents_have_roles() -> None:
    """Every agent in the shipped agents.json has a role file."""
    shipped = json.loads((TOOL_DIR / "agents.json").read_text(encoding="utf-8"))
    for agent in shipped["agents"]:
        assert (TOOL_DIR / "agents" / f"{agent['name']}.md").is_file()
        settings = agent.get("settings")
        if settings:
            assert (TOOL_DIR / settings).is_file()
