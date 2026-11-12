"""Tests for setting up Schlaue Antworten and answering a question."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.schlaue_antworten.const import (
    DOMAIN,
    SERVICE_ASK_QUESTION,
    SERVICE_INTERACTIVE_QUESTION,
    SERVICE_START_DIALOG,
)

from .conftest import ECHO, FakeAgents, SetupEntry

PRIMARY = "conversation.primary"
FALLBACK = "conversation.fallback"
OPTIONS = {
    "primary_agent": PRIMARY,
    "fallback_agent": FALLBACK,
    "enable_ha_context": False,
    "announce_model": False,
    "enable_detailed_followup": False,
}
SERVICES = (SERVICE_ASK_QUESTION, SERVICE_INTERACTIVE_QUESTION, SERVICE_START_DIALOG)


async def test_setup_and_unload(hass: HomeAssistant, setup_entry: SetupEntry) -> None:
    """Services exist while the entry is loaded and are gone after unloading."""
    entry = await setup_entry()
    assert entry.state is ConfigEntryState.LOADED
    for service in SERVICES:
        assert hass.services.has_service(DOMAIN, service)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    for service in SERVICES:
        assert not hass.services.has_service(DOMAIN, service)


async def test_answer_from_primary_agent(
    hass: HomeAssistant,
    setup_entry: SetupEntry,
    agents: FakeAgents,
    spoken: list[dict],
) -> None:
    """The primary agent answers and Alexa speaks it without markdown."""
    entry = await setup_entry(OPTIONS)
    agents.answers[PRIMARY] = "Der Mond ist **384.400 km** entfernt."

    manager = hass.data[DOMAIN][entry.entry_id]
    await manager.async_process_and_speak("Wie weit ist der Mond?", ECHO)
    await hass.async_block_till_done()

    assert [call["agent_id"] for call in agents.calls] == [PRIMARY]
    assert spoken[-1]["message"] == "Der Mond ist 384.400 km entfernt."
    assert spoken[-1]["target"] == [ECHO]
    assert manager.stats["today_count"] == 1


async def test_fallback_after_error(
    hass: HomeAssistant,
    setup_entry: SetupEntry,
    agents: FakeAgents,
    spoken: list[dict],
) -> None:
    """An overloaded primary agent hands the question to the fallback agent."""
    entry = await setup_entry(OPTIONS)
    agents.answers[PRIMARY] = "Error talking to API: 503 high demand"
    agents.answers[FALLBACK] = "Etwa 384.400 Kilometer."

    manager = hass.data[DOMAIN][entry.entry_id]
    await manager.async_process_and_speak("Wie weit ist der Mond?", ECHO)
    await hass.async_block_till_done()

    assert [call["agent_id"] for call in agents.calls] == [PRIMARY, FALLBACK]
    assert spoken[-1]["message"] == "Etwa 384.400 Kilometer."


async def test_both_agents_fail(
    hass: HomeAssistant,
    setup_entry: SetupEntry,
    agents: FakeAgents,
    spoken: list[dict],
) -> None:
    """Without any answer Alexa says the AI is overloaded."""
    entry = await setup_entry(OPTIONS)
    agents.answers[PRIMARY] = RuntimeError("down")
    agents.answers[FALLBACK] = ""

    manager = hass.data[DOMAIN][entry.entry_id]
    await manager.async_process_and_speak("Wie weit ist der Mond?", ECHO)
    await hass.async_block_till_done()

    assert "überlastet" in spoken[-1]["message"]
    assert manager.stats["today_count"] == 0
