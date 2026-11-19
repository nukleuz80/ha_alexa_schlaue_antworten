"""Tests for the bridge that hands voice prompts to a Claude session."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.setup import async_setup_component
import pytest

from custom_components.schlaue_antworten.claude_bridge import (
    RATE_LIMIT_PROMPTS,
    split_options,
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


async def _intent(client: Any, manager: Any, intent: str, text: str = "") -> str:
    response = await client.post(
        f"/api/webhook/{manager.skill.webhook_id}",
        json={
            "application_id": APP_ID,
            "action": "intent",
            "intent": intent,
            "text": text,
            "device_id": KITCHEN,
        },
    )
    return (await response.json())["speech"]


async def test_new_session_by_voice(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    aioclient_mock: Any,
    spoken: list[dict],
) -> None:
    """ "Neue Claude-Sitzung Heizung prüf das Bad" starts it with a first prompt."""
    aioclient_mock.post(f"{BRIDGE}/sessions", json={"session": "heizung"})
    manager = await _setup(hass, setup_entry, OPTIONS)
    client = await hass_client_no_auth()

    speech = await _intent(client, manager, "ClaudeNeuIntent", "Heizung prüf das Bad")
    assert speech == (
        "Okay, die Claude-Sitzung heizung startet. Die Antwort kommt gleich hier."
    )
    data = aioclient_mock.mock_calls[0][2]
    assert data["name"] == "heizung"
    assert data["text"] == "[Alexa · Test Echo] prüf das Bad"

    # The answer of that session is spoken with its name in front
    reply_url = data["reply_url"].removeprefix("http://192.168.1.10:8123")
    response = await client.post(
        reply_url, json={"text": "Das Ventil klemmt.", "session": "heizung"}
    )
    assert await response.json() == {"spoken": True}
    assert spoken[-1]["message"] == "heizung: Das Ventil klemmt."
    # An answer of the main session is not awaited
    response = await client.post(reply_url, json={"text": "Hallo"})
    assert await response.json() == {"spoken": False}


async def test_new_session_without_prompt_and_limits(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    aioclient_mock: Any,
) -> None:
    """Only a name starts an empty session; too many and the main one are refused."""
    aioclient_mock.post(f"{BRIDGE}/sessions", json={"session": "kueche"})
    manager = await _setup(hass, setup_entry, OPTIONS)
    client = await hass_client_no_auth()
    assert "kueche läuft" in await _intent(client, manager, "ClaudeNeuIntent", "Küche")
    assert "text" not in aioclient_mock.mock_calls[0][2]
    assert "Hauptsitzung bleibt" in await _intent(
        client, manager, "ClaudeNeuIntent", "alexa mach was"
    )
    assert "Wie soll" in await _intent(client, manager, "ClaudeNeuIntent", "")

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        f"{BRIDGE}/sessions",
        status=409,
        json={"sessions": ["alexa", "a", "b", "c"]},
    )
    assert await _intent(client, manager, "ClaudeNeuIntent", "d") == (
        "Es laufen schon zu viele Claude-Sitzungen. Beende zuerst eine. "
        "Es laufen: die Hauptsitzung, a, b und c."
    )


async def test_switch_list_and_end(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    aioclient_mock: Any,
) -> None:
    """Switching, listing and ending sessions by voice."""
    aioclient_mock.post(f"{BRIDGE}/switch", json={"active": "heizung"})
    aioclient_mock.get(
        f"{BRIDGE}/sessions", json={"sessions": ["alexa", "heizung"], "active": "heizung"}
    )
    aioclient_mock.post(f"{BRIDGE}/end", json={"ok": True})
    aioclient_mock.post(f"{BRIDGE}/prompt", json={"session": "heizung"})
    manager = await _setup(hass, setup_entry, OPTIONS)
    client = await hass_client_no_auth()

    assert await _intent(client, manager, "ClaudeWechselIntent", "Heizung") == (
        "Okay, Aufträge gehen jetzt an Claude heizung."
    )
    assert await _intent(client, manager, "ClaudeWechselIntent", "Hauptsitzung") == (
        "Okay, Aufträge gehen wieder an die Hauptsitzung."
    )
    assert await _intent(client, manager, "ClaudeListeIntent") == (
        "Es laufen: die Hauptsitzung und heizung. Aufträge gehen an heizung."
    )
    assert await _intent(client, manager, "ClaudeIntent", "mach weiter") == (
        "Okay, ist bei Claude heizung. Die Antwort kommt gleich hier."
    )
    assert await _intent(client, manager, "ClaudeEndeIntent", "Heizung") == (
        "Die Claude-Sitzung heizung ist beendet."
    )
    assert "Hauptsitzung bleibt" in await _intent(
        client, manager, "ClaudeEndeIntent", "alexa"
    )


async def test_unknown_session(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    aioclient_mock: Any,
) -> None:
    """An unknown name gets the list of running sessions."""
    aioclient_mock.post(f"{BRIDGE}/switch", status=404, json={"sessions": ["alexa"]})
    manager = await _setup(hass, setup_entry, OPTIONS)
    client = await hass_client_no_auth()
    assert await _intent(client, manager, "ClaudeWechselIntent", "garten") == (
        "Eine Claude-Sitzung garten gibt es nicht. Es laufen: die Hauptsitzung."
    )


def test_session_names() -> None:
    """Spoken names become short, plain session names."""
    from custom_components.schlaue_antworten.claude_bridge import (
        session_name,
        split_new_session,
    )

    assert session_name("Küche bitte") == "kueche"
    assert session_name("Hauptsitzung") == "alexa"
    assert session_name("") == ""
    assert split_new_session("Heizung  prüf das Bad") == ("heizung", "prüf das Bad")
    assert split_new_session("Garten") == ("garten", "")


async def test_alexa_app_sends_and_gets_push(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    aioclient_mock: Any,
    spoken: list[dict],
    pushes: list[dict],
) -> None:
    """The Alexa app, once marked as the phone, may send; answers come as push."""
    aioclient_mock.post(f"{BRIDGE}/prompt", json={"session": "alexa"})
    manager = await _setup(hass, setup_entry, {**OPTIONS, "claude_allow_app": True})
    client = await hass_client_no_auth()
    app = "amzn1.ask.device.PHONEAPP"

    async def post(intent: str, text: str = "") -> str:
        response = await client.post(
            f"/api/webhook/{manager.skill.webhook_id}",
            json={
                "application_id": APP_ID,
                "action": "intent",
                "intent": intent,
                "text": text,
                "device_id": app,
            },
        )
        return (await response.json())["speech"]

    assert "welcher Echo" in await post("ClaudeIntent", "mach was")
    assert "dein Handy" in await post("MeinHandyIntent")
    assert manager.skill.phone_devices == {app}
    assert await post("ClaudeIntent", "prüf die Fenster") == (
        "Okay, ist bei Claude. Die Antwort kommt aufs Handy."
    )
    data = aioclient_mock.mock_calls[-1][2]
    assert data["text"] == "[Alexa · Alexa-App] prüf die Fenster"

    response = await client.post(
        data["reply_url"].removeprefix("http://192.168.1.10:8123"),
        json={"text": "Alle Fenster sind zu.\n\n📊 Kontext: ~1 Tokens"},
    )
    assert await response.json() == {"spoken": True}
    await hass.async_block_till_done()
    assert spoken == []
    assert pushes[-1]["message"] == "Alle Fenster sind zu."


async def test_alexa_app_needs_the_option(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    aioclient_mock: Any,
) -> None:
    """Without "Alexa-App erlauben" the app is refused."""
    manager = await _setup(hass, setup_entry, OPTIONS)
    manager.skill._phones.add("amzn1.ask.device.PHONEAPP")
    client = await hass_client_no_auth()
    assert "darf ich Claude nichts" in await _say(
        client, manager, "mach was", device="amzn1.ask.device.PHONEAPP"
    )
    assert aioclient_mock.call_count == 0


def test_split_options() -> None:
    """The last "Optionen:" line becomes buttons and leaves the text."""
    assert split_options("Soll ich?\n\nOptionen: Ja | Nein") == ("Soll ich?", ["Ja", "Nein"])
    assert split_options("Text\n**Optionen:** A | B | C | D\n") == ("Text", ["A", "B", "C"])
    assert split_options("Optionen: Ja | Nein\nNoch was") == (
        "Optionen: Ja | Nein\nNoch was",
        [],
    )
    assert split_options("Keine Frage.") == ("Keine Frage.", [])


async def test_question_buttons_answer_goes_back(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    aioclient_mock: Any,
    spoken: list[dict],
    pushes: list[dict],
) -> None:
    """A question gets buttons; a tap sends the answer to the asking session."""
    aioclient_mock.post(f"{BRIDGE}/prompt", json={"session": "alexa"})
    manager = await _setup(hass, setup_entry, OPTIONS)
    client = await hass_client_no_auth()
    await _say(client, manager, "schalte das Licht aus")
    reply_url = aioclient_mock.mock_calls[-1][2]["reply_url"]

    response = await client.post(
        reply_url.removeprefix("http://192.168.1.10:8123"),
        json={"text": "Alle Lichter ausschalten?\n\nOptionen: Ja | Nein"},
    )
    assert await response.json() == {"spoken": True}
    await hass.async_block_till_done()
    assert spoken[-1]["message"].startswith("Alle Lichter ausschalten? Antworte")
    push = pushes[-1]
    assert push["message"] == "Alle Lichter ausschalten?"
    actions = push["data"]["actions"]
    assert [a["title"] for a in actions] == ["Ja", "Nein", "Antworten"]
    assert actions[2]["behavior"] == "textInput"

    hass.bus.async_fire(
        "mobile_app_notification_action", {"action": actions[0]["action"]}
    )
    await hass.async_block_till_done()
    data = aioclient_mock.mock_calls[-1][2]
    assert data["text"] == "[Alexa · Test Echo] Ja"
    assert data["session"] == "alexa"

    # The question is answered: a second tap does nothing
    calls = aioclient_mock.call_count
    hass.bus.async_fire(
        "mobile_app_notification_action", {"action": actions[1]["action"]}
    )
    await hass.async_block_till_done()
    assert aioclient_mock.call_count == calls


async def test_question_typed_answer(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    aioclient_mock: Any,
    spoken: list[dict],
    pushes: list[dict],
) -> None:
    """The text field of the push sends what was typed."""
    aioclient_mock.post(f"{BRIDGE}/prompt", json={"session": "alexa"})
    manager = await _setup(hass, setup_entry, OPTIONS)
    client = await hass_client_no_auth()
    await _say(client, manager, "räum auf")
    reply_url = aioclient_mock.mock_calls[-1][2]["reply_url"]
    await client.post(
        reply_url.removeprefix("http://192.168.1.10:8123"),
        json={"text": "Was genau?\nOptionen: Küche"},
    )
    await hass.async_block_till_done()
    reply = pushes[-1]["data"]["actions"][-1]["action"]
    hass.bus.async_fire(
        "mobile_app_notification_action",
        {"action": reply, "reply_text": "nur das Bad"},
    )
    await hass.async_block_till_done()
    assert aioclient_mock.mock_calls[-1][2]["text"] == "[Alexa · Test Echo] nur das Bad"
