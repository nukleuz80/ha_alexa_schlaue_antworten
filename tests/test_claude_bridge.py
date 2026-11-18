"""Tests for the bridge that hands voice prompts to a Claude session."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.setup import async_setup_component
import pytest

from custom_components.schlaue_antworten.claude_bridge import (
    RATE_LIMIT_PROMPTS,
    spoken_part,
)
from custom_components.schlaue_antworten.const import DOMAIN
from custom_components.schlaue_antworten.skill_model import build_interaction_model

from .conftest import ECHO, SetupEntry

APP_ID = "amzn1.ask.skill.mine"
BRIDGE = "http://192.168.1.50:8765"
KITCHEN = "amzn1.ask.device.KITCHEN123456"
OPTIONS = {
    "voice_path": "skill",
    "primary_agent": "conversation.primary",
    "fallback_agent": "conversation.fallback",
    "claude_url": BRIDGE + "/",
    "claude_token": "geheim",
    "claude_echos": [ECHO],
}


@pytest.fixture(autouse=True)
async def http(hass: HomeAssistant) -> None:
    """Load the HTTP stack and give Home Assistant a local address."""
    assert await async_setup_component(hass, "webhook", {})
    hass.config.internal_url = "http://192.168.1.10:8123"


@pytest.fixture
def pushes(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Record pushes to the phone."""
    calls: list[dict[str, Any]] = []

    async def _record(call: ServiceCall) -> None:
        calls.append(dict(call.data))

    hass.services.async_register("notify", "notify", _record)
    return calls


async def _setup(
    hass: HomeAssistant, setup_entry: SetupEntry, options: dict[str, Any]
) -> Any:
    entry = await setup_entry(options)
    manager = hass.data[DOMAIN][entry.entry_id]
    # The asking Echo is assigned, as after "Du stehst in der Küche"
    manager.skill._seen[KITCHEN] = "2026-11-18 20:00"
    await manager.skill.async_set_device_map({KITCHEN: ECHO})
    return manager


async def _say(client: Any, manager: Any, text: str, device: str = KITCHEN) -> str:
    response = await client.post(
        f"/api/webhook/{manager.skill.webhook_id}",
        json={
            "application_id": APP_ID,
            "action": "intent",
            "intent": "ClaudeIntent",
            "text": text,
            "device_id": device,
        },
    )
    return (await response.json())["speech"]


async def test_prompt_goes_to_claude_and_answer_comes_back(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    aioclient_mock: Any,
    spoken: list[dict],
    pushes: list[dict],
) -> None:
    """The prompt reaches the bridge; the answer is spoken on the asking Echo."""
    aioclient_mock.post(f"{BRIDGE}/prompt", json={"ok": True})
    manager = await _setup(hass, setup_entry, OPTIONS)
    client = await hass_client_no_auth()

    speech = await _say(client, manager, "prüf  mal die Fenster")
    assert speech.startswith("Okay, ist bei Claude")
    _method, url, data, headers = aioclient_mock.mock_calls[0]
    assert str(url) == f"{BRIDGE}/prompt"
    assert headers["Authorization"] == "Bearer geheim"
    assert data["text"] == "[Alexa · Test Echo] prüf mal die Fenster"
    reply_url = data["reply_url"]
    assert reply_url.startswith("http://192.168.1.10:8123/api/webhook/")

    answer = "**Alle Fenster** sind zu.\n\n| Raum | Status |\n|---|---|\n| Bad | zu |"
    response = await client.post(
        reply_url.removeprefix("http://192.168.1.10:8123"), json={"text": answer}
    )
    assert await response.json() == {"spoken": True}
    await hass.async_block_till_done()
    assert spoken[-1]["target"] == [ECHO]
    assert spoken[-1]["data"] == {"type": "announce"}
    assert spoken[-1]["message"].startswith("Alle Fenster sind zu.")
    assert "aufs Handy" in spoken[-1]["message"]
    assert pushes[-1]["message"] == answer

    # A second answer without a new voice prompt stays quiet
    count = len(spoken)
    response = await client.post(
        reply_url.removeprefix("http://192.168.1.10:8123"), json={"text": "Noch was"}
    )
    assert await response.json() == {"spoken": False}
    assert len(spoken) == count


async def test_short_answer_is_not_pushed(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    aioclient_mock: Any,
    spoken: list[dict],
    pushes: list[dict],
) -> None:
    """A one-sentence answer is only spoken."""
    aioclient_mock.post(f"{BRIDGE}/prompt", json={"ok": True})
    manager = await _setup(hass, setup_entry, OPTIONS)
    client = await hass_client_no_auth()
    await _say(client, manager, "wie spät ist es")
    reply_url = aioclient_mock.mock_calls[0][2]["reply_url"]
    await client.post(
        reply_url.removeprefix("http://192.168.1.10:8123"),
        json={"text": "Es ist 21 Uhr."},
    )
    await hass.async_block_till_done()
    assert spoken[-1]["message"] == "Es ist 21 Uhr."
    assert pushes == []


async def test_only_allowed_and_known_echos(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    aioclient_mock: Any,
) -> None:
    """Unknown devices and Echos not on the list never reach the bridge."""
    aioclient_mock.post(f"{BRIDGE}/prompt", json={"ok": True})
    manager = await _setup(hass, setup_entry, {**OPTIONS, "claude_echos": []})
    client = await hass_client_no_auth()

    assert "darf ich Claude nichts" in await _say(client, manager, "mach was")
    # Not assigned: the default Echo must not count
    assert "welcher Echo das ist" in await _say(
        client, manager, "mach was", device="amzn1.ask.device.OTHER"
    )
    assert aioclient_mock.call_count == 0


async def test_switch_turns_the_bridge_off(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    aioclient_mock: Any,
) -> None:
    """With the switch off nothing goes out."""
    aioclient_mock.post(f"{BRIDGE}/prompt", json={"ok": True})
    manager = await _setup(hass, setup_entry, OPTIONS)
    client = await hass_client_no_auth()
    switch = "switch.alexa_schlaue_antworten_claude_brucke"
    assert hass.states.get(switch).state == "on"
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": switch}, blocking=True
    )
    assert hass.states.get(switch).state == "off"
    assert "ausgeschaltet" in await _say(client, manager, "mach was")
    assert aioclient_mock.call_count == 0


async def test_not_set_up_unreachable_and_rate_limit(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    aioclient_mock: Any,
) -> None:
    """Missing setup, a dead bridge and too many prompts are spoken plainly."""
    aioclient_mock.post(f"{BRIDGE}/prompt", status=500)
    manager = await _setup(hass, setup_entry, OPTIONS)
    client = await hass_client_no_auth()
    assert "nicht erreichbar" in await _say(client, manager, "mach was")

    aioclient_mock.clear_requests()
    aioclient_mock.post(f"{BRIDGE}/prompt", json={"ok": True})
    for _ in range(RATE_LIMIT_PROMPTS):
        assert "bei Claude" in await _say(client, manager, "mach was")
    assert "zu viele" in await _say(client, manager, "mach was")


async def test_without_setup(
    hass: HomeAssistant, hass_client_no_auth: Any, setup_entry: SetupEntry
) -> None:
    """Without address and token the Echo says how to set it up."""
    options = {k: v for k, v in OPTIONS.items() if not k.startswith("claude")}
    manager = await _setup(hass, setup_entry, options)
    client = await hass_client_no_auth()
    assert "noch nicht eingerichtet" in await _say(client, manager, "mach was")


def test_spoken_part() -> None:
    """Only the first paragraph is spoken, without markup."""
    assert spoken_part("# Titel\n\nRest") == "Titel"
    assert spoken_part("Siehe [Doku](http://x) und `code`.") == "Siehe Doku und code."
    long = "Satz eins ist da. " * 40
    part = spoken_part(long)
    assert len(part) <= 400
    assert part.endswith(".")


def test_interaction_model_has_claude_intent() -> None:
    """The voice model offers "Claude soll ..."."""
    intents = {
        intent["name"]: intent
        for intent in build_interaction_model("schlaufuchs")["interactionModel"][
            "languageModel"
        ]["intents"]
    }
    assert "claude soll {frage}" in intents["ClaudeIntent"]["samples"]
