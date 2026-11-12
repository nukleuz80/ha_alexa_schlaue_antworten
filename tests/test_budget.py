"""Tests for the time budget and the late answer by push."""
from __future__ import annotations

import asyncio
from typing import Any

import pytest
from homeassistant.core import HomeAssistant, ServiceCall

from custom_components.schlaue_antworten.const import DEFAULT_LATE_TEXT, DOMAIN

from .conftest import ECHO, FakeAgents, SetupEntry
from .test_init import OPTIONS, PRIMARY

SLOW = {**OPTIONS, "fallback_agent": "", "answer_budget": 0.2, "enable_logging": True}


@pytest.fixture
def pushed(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Record push messages sent to notify.notify."""
    calls: list[dict[str, Any]] = []

    async def _record(call: ServiceCall) -> None:
        calls.append(dict(call.data))

    hass.services.async_register("notify", "notify", _record)
    return calls


async def test_late_answer_goes_to_phone(
    hass: HomeAssistant,
    setup_entry: SetupEntry,
    agents: FakeAgents,
    spoken: list[dict],
    pushed: list[dict],
) -> None:
    """Alexa says the late text at once and the answer follows by push."""
    entry = await setup_entry(SLOW)
    agents.answers[PRIMARY] = "Der Mond ist 384.400 km entfernt."
    agents.delays[PRIMARY] = 0.6
    manager = hass.data[DOMAIN][entry.entry_id]

    await manager.async_process_and_speak("Wie weit ist der Mond?", ECHO)
    assert [call["message"] for call in spoken] == [DEFAULT_LATE_TEXT]
    assert pushed == []

    await hass.async_block_till_done()
    assert pushed[0]["message"] == "Der Mond ist 384.400 km entfernt."
    assert "Wie weit ist der Mond?" in pushed[0]["title"]
    # No spoken confirmation on top of the late text
    assert len(spoken) == 1
    assert manager.stats["today_count"] == 1
    assert "[Spät]" in manager.get_history_markdown()


async def test_late_error_sends_nothing(
    hass: HomeAssistant,
    setup_entry: SetupEntry,
    agents: FakeAgents,
    spoken: list[dict],
    pushed: list[dict],
) -> None:
    """A late failure is only logged."""
    entry = await setup_entry(SLOW)
    agents.answers[PRIMARY] = RuntimeError("down")
    agents.delays[PRIMARY] = 0.6
    manager = hass.data[DOMAIN][entry.entry_id]

    await manager.async_process_and_speak("Frage?", ECHO)
    await hass.async_block_till_done()
    assert pushed == []
    assert manager.stats["today_count"] == 0


async def test_answer_within_budget(
    hass: HomeAssistant,
    setup_entry: SetupEntry,
    agents: FakeAgents,
    spoken: list[dict],
    pushed: list[dict],
) -> None:
    """A fast answer is spoken as usual."""
    entry = await setup_entry({**SLOW, "answer_budget": 2})
    agents.answers[PRIMARY] = "Schnell."
    manager = hass.data[DOMAIN][entry.entry_id]

    await manager.async_process_and_speak("Frage?", ECHO)
    await hass.async_block_till_done()
    assert [call["message"] for call in spoken] == ["Schnell."]
    assert pushed == []


async def test_no_budget(
    hass: HomeAssistant,
    setup_entry: SetupEntry,
    agents: FakeAgents,
    spoken: list[dict],
    pushed: list[dict],
) -> None:
    """With 0 seconds Alexa waits as long as the AI needs."""
    entry = await setup_entry({**SLOW, "answer_budget": 0})
    agents.answers[PRIMARY] = "Langsam, aber da."
    agents.delays[PRIMARY] = 0.4
    manager = hass.data[DOMAIN][entry.entry_id]

    await manager.async_process_and_speak("Frage?", ECHO)
    assert [call["message"] for call in spoken] == ["Langsam, aber da."]


async def test_unload_cancels_late_answer(
    hass: HomeAssistant,
    setup_entry: SetupEntry,
    agents: FakeAgents,
    spoken: list[dict],
    pushed: list[dict],
) -> None:
    """Unloading stops an answer that is still on its way."""
    entry = await setup_entry(SLOW)
    agents.answers[PRIMARY] = "Zu spät."
    agents.delays[PRIMARY] = 30
    manager = hass.data[DOMAIN][entry.entry_id]

    await manager.async_process_and_speak("Frage?", ECHO)
    tasks = set(manager._background_tasks)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await asyncio.wait(tasks, timeout=5)
    assert all(task.cancelled() for task in tasks)
    assert agents.cancelled == [PRIMARY]
    assert pushed == []
