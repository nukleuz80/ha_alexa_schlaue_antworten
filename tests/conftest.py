"""Fixtures for Schlaue Antworten tests."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.schlaue_antworten.const import DOMAIN

ECHO = "media_player.test_echo"

SetupEntry = Callable[..., Awaitable[MockConfigEntry]]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading of custom integrations in all tests."""


@pytest.fixture(autouse=True)
def german_home_assistant(request: pytest.FixtureRequest) -> None:
    """Run tests with German settings, as all spoken texts are German."""
    if "hass" in request.fixturenames:
        request.getfixturevalue("hass").config.language = "de"


@pytest.fixture
def setup_entry(hass: HomeAssistant) -> SetupEntry:
    """Return a helper that sets up a config entry with the given options."""

    async def _setup(options: dict[str, Any] | None = None) -> MockConfigEntry:
        hass.states.async_set(ECHO, "idle", {"friendly_name": "Test Echo"})
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Schlaue Antworten",
            data={},
            options={"default_echo": ECHO, **(options or {})},
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        return entry

    return _setup


class FakeAgents:
    """Stand-in for conversation.process with one answer per agent."""

    def __init__(self) -> None:
        # An answer may depend on the prompt: a callable gets the prompt text
        self.answers: dict[str, str | Exception | Callable[[str], str]] = {}
        self.delays: dict[str, float] = {}
        self.calls: list[dict[str, Any]] = []
        self.cancelled: list[str] = []

    async def handle(self, call: ServiceCall) -> dict[str, Any]:
        self.calls.append(dict(call.data))
        agent_id = call.data["agent_id"]
        try:
            await asyncio.sleep(self.delays.get(agent_id, 0))
        except asyncio.CancelledError:
            self.cancelled.append(agent_id)
            raise
        answer = self.answers.get(call.data["agent_id"], "")
        if callable(answer) and not isinstance(answer, Exception):
            answer = answer(call.data["text"])
        if isinstance(answer, Exception):
            raise answer
        return {"response": {"speech": {"plain": {"speech": answer}}}}


@pytest.fixture
def agents(hass: HomeAssistant) -> FakeAgents:
    """Register a fake conversation.process service."""
    fake = FakeAgents()
    hass.services.async_register(
        "conversation",
        "process",
        fake.handle,
        supports_response=SupportsResponse.ONLY,
    )
    return fake


@pytest.fixture
def spoken(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Record everything sent to notify.alexa_media."""
    calls: list[dict[str, Any]] = []

    async def _record(call: ServiceCall) -> None:
        calls.append(dict(call.data))

    hass.services.async_register("notify", "alexa_media", _record)
    return calls
