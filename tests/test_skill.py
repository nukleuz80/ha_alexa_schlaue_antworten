"""Tests for the webhook that the own Alexa skill calls."""
from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
import pytest

from custom_components.schlaue_antworten.const import DOMAIN
from custom_components.schlaue_antworten.skill import (
    RATE_LIMIT_REQUESTS,
    SKILL_STORAGE_KEY,
)

from .conftest import FakeAgents, SetupEntry

PRIMARY = "conversation.primary"
FALLBACK = "conversation.fallback"
APP_ID = "amzn1.ask.skill.mine"
OPTIONS = {
    "voice_path": "skill",
    "primary_agent": PRIMARY,
    "fallback_agent": FALLBACK,
    "enable_ha_context": False,
    "announce_model": False,
    "enable_detailed_followup": False,
}


@pytest.fixture(autouse=True)
async def http(hass: HomeAssistant) -> None:
    """Load the HTTP stack the webhook needs."""
    assert await async_setup_component(hass, "webhook", {})


def _ask(text: str, application_id: str = APP_ID, **extra: Any) -> dict[str, Any]:
    return {"application_id": application_id, "action": "ask", "text": text, **extra}


async def test_answer_comes_back_in_the_reply(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    agents: FakeAgents,
    spoken: list[dict],
    hass_storage: dict[str, Any],
) -> None:
    """The skill gets the answer as JSON, nothing goes through Alexa Media."""
    entry = await setup_entry(OPTIONS)
    agents.answers[PRIMARY] = "Der Mond ist **384.400 km** entfernt."
    manager = hass.data[DOMAIN][entry.entry_id]
    client = await hass_client_no_auth()

    response = await client.post(
        f"/api/webhook/{manager.skill.webhook_id}",
        json=_ask("Wie weit ist der Mond?", device_id="amzn1.device.x"),
    )
    assert response.status == 200
    assert await response.json() == {
        "speech": "Der Mond ist 384.400 km entfernt.",
        "end_session": True,
    }
    assert spoken == []
    assert manager.skill.is_linked
    assert manager.stats["last_path"] == "skill"
    assert manager.stats["last_device"] == "Test Echo"
    await hass.async_block_till_done()
    assert hass_storage[SKILL_STORAGE_KEY]["data"]["application_id"] == APP_ID


async def test_only_the_first_skill_is_accepted(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    agents: FakeAgents,
) -> None:
    """After linking, requests from any other skill are refused."""
    entry = await setup_entry(OPTIONS)
    agents.answers[PRIMARY] = "Antwort."
    url = f"/api/webhook/{hass.data[DOMAIN][entry.entry_id].skill.webhook_id}"
    client = await hass_client_no_auth()

    assert (await client.post(url, json=_ask("Wer war Goethe?"))).status == 200
    other = await client.post(url, json=_ask("Wer war Goethe?", "amzn1.ask.skill.x"))
    assert other.status == 403


@pytest.mark.parametrize(
    "payload",
    [
        {"action": "ask", "text": "Hallo du"},
        {"application_id": APP_ID, "action": "delete", "text": "Hallo du"},
        {"application_id": APP_ID, "action": "ask", "text": 5},
        {"application_id": APP_ID, "action": "ask", "text": "Hi", "device_id": 3},
        ["no", "dict"],
    ],
)
async def test_invalid_requests(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    agents: FakeAgents,
    payload: Any,
) -> None:
    """Malformed requests are rejected and do not link a skill."""
    entry = await setup_entry(OPTIONS)
    manager = hass.data[DOMAIN][entry.entry_id]
    client = await hass_client_no_auth()
    response = await client.post(
        f"/api/webhook/{manager.skill.webhook_id}", json=payload
    )
    assert response.status == 400
    assert not manager.skill.is_linked
    assert agents.calls == []


async def test_rate_limit(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    agents: FakeAgents,
) -> None:
    """Too many questions within a minute are slowed down."""
    entry = await setup_entry(OPTIONS)
    agents.answers[PRIMARY] = "Antwort."
    url = f"/api/webhook/{hass.data[DOMAIN][entry.entry_id].skill.webhook_id}"
    client = await hass_client_no_auth()
    for number in range(RATE_LIMIT_REQUESTS):
        assert (await client.post(url, json=_ask(f"Frage {number}"))).status == 200
    assert (await client.post(url, json=_ask("Noch eine"))).status == 429


async def test_too_slow_answer_says_late_text(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    agents: FakeAgents,
) -> None:
    """The skill never waits longer than its budget; the answer follows by push."""
    pushed: list[dict[str, Any]] = []

    async def _push(call: Any) -> None:
        pushed.append(dict(call.data))

    hass.services.async_register("notify", "notify", _push)
    entry = await setup_entry(
        {**OPTIONS, "answer_budget": 0.3, "primary_timeout": 0, "fallback_agent": ""}
    )
    agents.answers[PRIMARY] = "Spät, aber richtig."
    agents.delays[PRIMARY] = 0.8
    url = f"/api/webhook/{hass.data[DOMAIN][entry.entry_id].skill.webhook_id}"
    client = await hass_client_no_auth()

    response = await client.post(url, json=_ask("Wie weit ist der Mond?"))
    assert (await response.json())["speech"].startswith("Das dauert gerade zu lange")
    await hass.async_block_till_done(wait_background_tasks=True)
    for _ in range(20):
        if pushed:
            break
        await asyncio.sleep(0.1)
    assert pushed and "Spät, aber richtig." in str(pushed[-1])


async def test_overloaded_answer(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    agents: FakeAgents,
) -> None:
    """Without any agent answer the skill says the AI is overloaded."""
    entry = await setup_entry(OPTIONS)
    agents.answers[PRIMARY] = RuntimeError("down")
    agents.answers[FALLBACK] = ""
    url = f"/api/webhook/{hass.data[DOMAIN][entry.entry_id].skill.webhook_id}"
    client = await hass_client_no_auth()
    response = await client.post(url, json=_ask("Wie weit ist der Mond?"))
    assert "überlastet" in (await response.json())["speech"]


async def test_reset_replaces_the_secret(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    agents: FakeAgents,
) -> None:
    """The reset button invalidates the old address and the skill link."""
    entry = await setup_entry(OPTIONS)
    agents.answers[PRIMARY] = "Antwort."
    manager = hass.data[DOMAIN][entry.entry_id]
    old_url = f"/api/webhook/{manager.skill.webhook_id}"
    client = await hass_client_no_auth()
    assert (await client.post(old_url, json=_ask("Wer war Goethe?"))).status == 200

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.alexa_schlaue_antworten_skill_kopplung_zurucksetzen"},
        blocking=True,
    )
    assert not manager.skill.is_linked
    assert f"/api/webhook/{manager.skill.webhook_id}" != old_url
    # Home Assistant answers unknown webhooks with 200 but does nothing
    await client.post(old_url, json=_ask("Wer war Goethe?", "amzn1.ask.skill.x"))
    assert not manager.skill.is_linked


async def test_community_path_has_no_webhook(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    agents: FakeAgents,
) -> None:
    """With the default voice path the webhook stays off."""
    entry = await setup_entry({**OPTIONS, "voice_path": "community"})
    manager = hass.data[DOMAIN][entry.entry_id]
    assert not manager.skill.is_active
    assert manager.uses_community


async def test_unload_stops_the_webhook(
    hass: HomeAssistant, setup_entry: SetupEntry, agents: FakeAgents
) -> None:
    """Unloading removes the webhook again."""
    entry = await setup_entry({**OPTIONS, "voice_path": "both"})
    manager = hass.data[DOMAIN][entry.entry_id]
    assert manager.skill.is_active and manager.uses_community
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert not manager.skill.is_active
