"""Tests for the race between the primary and the fallback agent."""
from __future__ import annotations

import time

from homeassistant.core import HomeAssistant

from custom_components.schlaue_antworten.const import DOMAIN

from .conftest import ECHO, FakeAgents, SetupEntry
from .test_init import FALLBACK, OPTIONS, PRIMARY


async def _answer(hass: HomeAssistant, entry_id: str):
    started = time.monotonic()
    result = await hass.data[DOMAIN][entry_id].answers.async_answer("Frage?", ECHO)
    await hass.async_block_till_done()
    return result, time.monotonic() - started


async def test_slow_primary_loses_to_fallback(
    hass: HomeAssistant, setup_entry: SetupEntry, agents: FakeAgents
) -> None:
    """A hanging primary agent is overtaken and then cancelled."""
    entry = await setup_entry({**OPTIONS, "primary_timeout": 0.2})
    agents.answers = {PRIMARY: "langsam", FALLBACK: "schnell"}
    agents.delays = {PRIMARY: 5}

    result, elapsed = await _answer(hass, entry.entry_id)
    assert result.text == "schnell"
    assert result.agent == FALLBACK
    assert elapsed < 1.5
    assert agents.cancelled == [PRIMARY]
    assert set(result.agent_seconds) == {PRIMARY, FALLBACK}


async def test_primary_still_wins_after_timeout(
    hass: HomeAssistant, setup_entry: SetupEntry, agents: FakeAgents
) -> None:
    """After the time limit both run, and the primary agent may still be first."""
    entry = await setup_entry({**OPTIONS, "primary_timeout": 0.1})
    agents.answers = {PRIMARY: "primär", FALLBACK: "fallback"}
    agents.delays = {PRIMARY: 0.3, FALLBACK: 2}

    result, elapsed = await _answer(hass, entry.entry_id)
    assert result.agent == PRIMARY
    assert elapsed < 1.5
    assert agents.cancelled == [FALLBACK]


async def test_error_starts_fallback_at_once(
    hass: HomeAssistant, setup_entry: SetupEntry, agents: FakeAgents
) -> None:
    """An error does not wait for the time limit."""
    entry = await setup_entry({**OPTIONS, "primary_timeout": 10})
    agents.answers = {PRIMARY: "503 Service Unavailable", FALLBACK: "fallback"}

    result, elapsed = await _answer(hass, entry.entry_id)
    assert result.agent == FALLBACK
    assert elapsed < 1.5


async def test_no_race_with_zero_timeout(
    hass: HomeAssistant, setup_entry: SetupEntry, agents: FakeAgents
) -> None:
    """With 0 seconds the fallback only runs after an error."""
    entry = await setup_entry({**OPTIONS, "primary_timeout": 0})
    agents.answers = {PRIMARY: "primär", FALLBACK: "fallback"}
    agents.delays = {PRIMARY: 0.4}

    result, _elapsed = await _answer(hass, entry.entry_id)
    assert result.agent == PRIMARY
    assert [call["agent_id"] for call in agents.calls] == [PRIMARY]


async def test_without_fallback_agent(
    hass: HomeAssistant, setup_entry: SetupEntry, agents: FakeAgents
) -> None:
    """Without a fallback the primary agent is simply awaited."""
    entry = await setup_entry(
        {**OPTIONS, "fallback_agent": "", "primary_timeout": 0.1}
    )
    agents.answers = {PRIMARY: "primär"}
    agents.delays = {PRIMARY: 0.3}

    result, _elapsed = await _answer(hass, entry.entry_id)
    assert result.agent == PRIMARY
    assert not result.error


async def test_both_fail_in_race(
    hass: HomeAssistant, setup_entry: SetupEntry, agents: FakeAgents
) -> None:
    """If neither agent gives a valid answer the result is an error."""
    entry = await setup_entry({**OPTIONS, "primary_timeout": 0.1})
    agents.answers = {PRIMARY: "", FALLBACK: RuntimeError("down")}
    agents.delays = {PRIMARY: 0.3}

    result, _elapsed = await _answer(hass, entry.entry_id)
    assert result.error
