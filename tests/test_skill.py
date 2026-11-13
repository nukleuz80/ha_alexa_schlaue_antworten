"""Tests for the webhook that the own Alexa skill calls."""
from __future__ import annotations

import asyncio
import time
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


async def test_skill_actions(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    agents: FakeAgents,
) -> None:
    """Launch, question intents and the built-in intents get the right reply."""
    entry = await setup_entry(OPTIONS)
    agents.answers[PRIMARY] = "Etwa 384.400 Kilometer."
    url = f"/api/webhook/{hass.data[DOMAIN][entry.entry_id].skill.webhook_id}"
    client = await hass_client_no_auth()

    async def post(**payload: Any) -> dict[str, Any]:
        response = await client.post(url, json={"application_id": APP_ID, **payload})
        assert response.status == 200
        return await response.json()

    launch = await post(action="launch")
    assert launch["end_session"] is False and launch["reprompt"]

    answer = await post(action="intent", intent="WieIntent", text="weit ist der mond")
    assert answer == {"speech": "Etwa 384.400 Kilometer.", "end_session": True}
    assert "wie weit ist der mond" in agents.calls[-1]["text"]

    stop = await post(action="intent", intent="AMAZON.StopIntent")
    assert stop["end_session"] is True
    helping = await post(action="intent", intent="AMAZON.HelpIntent")
    assert helping["end_session"] is False
    unclear = await post(action="intent", intent="AMAZON.FallbackIntent")
    assert unclear["end_session"] is False and "nicht verstanden" in unclear["speech"]
    empty = await post(action="intent", intent="WasIntent", text="")
    assert empty["end_session"] is False
    phone = await post(action="intent", intent="HandyIntent")
    assert phone["end_session"] is True
    assert len(agents.calls) == 1


async def test_dialog_stays_open(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    agents: FakeAgents,
) -> None:
    """With an open dialog three questions follow without saying Alexa again."""
    entry = await setup_entry({**OPTIONS, "skill_keep_open": True})
    agents.answers[PRIMARY] = "Antwort."
    url = f"/api/webhook/{hass.data[DOMAIN][entry.entry_id].skill.webhook_id}"
    client = await hass_client_no_auth()

    async def post(**payload: Any) -> dict[str, Any]:
        response = await client.post(url, json={"application_id": APP_ID, **payload})
        return await response.json()

    assert (await post(action="launch"))["end_session"] is False
    for word, rest in (("WerIntent", "war goethe"), ("WasIntent", "ist ein quark")):
        reply = await post(action="intent", intent=word, text=rest)
        assert reply == {
            "speech": "Antwort. Noch eine Frage?",
            "end_session": False,
            "reprompt": "Noch eine Frage?",
        }
    yes = await post(action="intent", intent="AMAZON.YesIntent")
    assert yes["speech"] == "Was möchtest du wissen?" and yes["end_session"] is False
    third = await post(action="intent", intent="WieIntent", text="weit ist der mond")
    assert third["end_session"] is False
    no = await post(action="intent", intent="AMAZON.NoIntent")
    assert no == {"speech": "Alles klar.", "end_session": True}
    assert len(agents.calls) == 3


async def test_detail_on_yes(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    agents: FakeAgents,
) -> None:
    """After a short answer Alexa offers more; "Ja" brings the detailed answer.

    The detailed answer is computed while Alexa asks "Ja oder Nein?".
    """
    entry = await setup_entry({**OPTIONS, "enable_detailed_followup": True})
    manager = hass.data[DOMAIN][entry.entry_id]
    url = f"/api/webhook/{manager.skill.webhook_id}"
    client = await hass_client_no_auth()

    async def post(**payload: Any) -> dict[str, Any]:
        response = await client.post(url, json={"application_id": APP_ID, **payload})
        return await response.json()

    agents.answers[PRIMARY] = lambda prompt: (
        "Der Mond kreist in etwa 384.400 Kilometern um uns."
        if "Ergänze" in prompt
        else "Etwa 384.400 Kilometer."
    )
    short = await post(action="intent", intent="WieIntent", text="weit ist der mond")
    assert short["speech"].startswith("Etwa 384.400 Kilometer. Möchtest du")
    assert short["end_session"] is False
    session = short["session"]
    assert session["stage"] == "followup"
    assert session["question"] == "wie weit ist der mond"
    assert session["answer"] == "Etwa 384.400 Kilometer."
    assert session["detail"]

    await hass.async_block_till_done()
    calls_before_yes = len(agents.calls)
    detail = await post(action="intent", intent="AMAZON.YesIntent", session=session)
    assert detail == {
        "speech": "Der Mond kreist in etwa 384.400 Kilometern um uns.",
        "end_session": True,
    }
    # The answer computed ahead was used; "Ja" did not ask the AI again
    assert len(agents.calls) == calls_before_yes
    # Both agents raced for the detailed answer, with the short answer as context
    detail_calls = [call for call in agents.calls if "Ergänze" in call["text"]]
    assert {call["agent_id"] for call in detail_calls} == {PRIMARY, FALLBACK}
    assert "Etwa 384.400 Kilometer." in detail_calls[0]["text"]
    assert manager.stats["today_detailed"] == 1

    # A "Ja" from an old session without a computed answer asks the AI itself
    old = {key: value for key, value in session.items() if key != "detail"}
    again = await post(action="intent", intent="AMAZON.YesIntent", session=old)
    assert again["speech"] == "Der Mond kreist in etwa 384.400 Kilometern um uns."
    assert len(agents.calls) > calls_before_yes


async def test_no_cancels_the_detail(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    agents: FakeAgents,
) -> None:
    """"Nein" stops the detailed answer that was computed ahead."""
    entry = await setup_entry({**OPTIONS, "enable_detailed_followup": True})
    url = f"/api/webhook/{hass.data[DOMAIN][entry.entry_id].skill.webhook_id}"
    client = await hass_client_no_auth()
    agents.answers[PRIMARY] = "Etwa 384.400 Kilometer."
    agents.delays[PRIMARY] = 0
    agents.delays[FALLBACK] = 5

    async def post(**payload: Any) -> dict[str, Any]:
        response = await client.post(url, json={"application_id": APP_ID, **payload})
        return await response.json()

    short = await post(action="intent", intent="WieIntent", text="weit ist der mond")
    agents.delays[PRIMARY] = 5
    no = await post(action="intent", intent="AMAZON.NoIntent", session=short["session"])
    assert no == {"speech": "Alles klar.", "end_session": True}
    await hass.async_block_till_done()
    assert PRIMARY in agents.cancelled or FALLBACK in agents.cancelled


async def test_late_detail_counts_as_detailed(
    hass: HomeAssistant, setup_entry: SetupEntry, agents: FakeAgents
) -> None:
    """A detailed answer that arrives late by push counts as a detailed answer."""
    hass.services.async_register("notify", "notify", lambda call: None)
    entry = await setup_entry({**OPTIONS, "answer_budget": 0.2})
    manager = hass.data[DOMAIN][entry.entry_id]
    agents.answers[PRIMARY] = "Ausführlich."
    agents.delays[PRIMARY] = 0.5
    result = await manager.async_answer_within_budget(
        "wer war goethe",
        "media_player.test_echo",
        is_followup=True,
        previous_answer="Ein Dichter.",
        start_time=time.monotonic(),
        path="skill",
    )
    assert result is None
    for _ in range(30):
        if manager.stats["today_detailed"]:
            break
        await asyncio.sleep(0.1)
    assert manager.stats["today_detailed"] == 1
    assert "[Spät] [Vertiefung] wer war goethe" in manager.get_history_markdown()


async def test_no_detail_keeps_dialog_open(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    agents: FakeAgents,
) -> None:
    """With an open dialog "Nein" to more detail asks for the next question."""
    entry = await setup_entry(
        {**OPTIONS, "enable_detailed_followup": True, "skill_keep_open": True}
    )
    url = f"/api/webhook/{hass.data[DOMAIN][entry.entry_id].skill.webhook_id}"
    client = await hass_client_no_auth()
    session = {
        "stage": "followup",
        "question": "wer war goethe",
        "answer": "Ein Dichter.",
    }
    response = await client.post(
        url,
        json={
            "application_id": APP_ID,
            "action": "intent",
            "intent": "AMAZON.NoIntent",
            "session": session,
        },
    )
    reply = await response.json()
    assert reply["speech"] == "Noch eine Frage?" and reply["end_session"] is False
    # A "Ja" without a stored question just asks what the user wants to know
    response = await client.post(
        url,
        json={
            "application_id": APP_ID,
            "action": "intent",
            "intent": "AMAZON.YesIntent",
        },
    )
    assert (await response.json())["speech"] == "Was möchtest du wissen?"
    assert agents.calls == []


async def test_no_endless_fallback(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    agents: FakeAgents,
) -> None:
    """The second sentence Alexa cannot match ends the dialog."""
    entry = await setup_entry(OPTIONS)
    url = f"/api/webhook/{hass.data[DOMAIN][entry.entry_id].skill.webhook_id}"
    client = await hass_client_no_auth()

    async def post(**payload: Any) -> dict[str, Any]:
        response = await client.post(
            url,
            json={"application_id": APP_ID, "action": "intent", **payload},
        )
        return await response.json()

    first = await post(intent="AMAZON.FallbackIntent")
    assert first["end_session"] is False
    assert first["session"] == {"retries": 1}
    second = await post(intent="AMAZON.FallbackIntent", session=first["session"])
    assert second["end_session"] is True
    assert "wieder nicht verstehen" in second["speech"]

    state = hass.states.get("sensor.alexa_schlaue_antworten_ki_anfragen_heute")
    last = state.attributes["letzte_skill_anfrage"]
    assert last["intent"] == "AMAZON.FallbackIntent"
    assert last["offen"] == "False"


async def test_start_intent_and_invocation_question(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    setup_entry: SetupEntry,
    agents: FakeAgents,
) -> None:
    """"öffne schlaufuchs" and "frag schlaufuchs ..." also work in an open dialog."""
    entry = await setup_entry(OPTIONS)
    agents.answers[PRIMARY] = "Ein Dichter."
    url = f"/api/webhook/{hass.data[DOMAIN][entry.entry_id].skill.webhook_id}"
    client = await hass_client_no_auth()

    async def post(**payload: Any) -> dict[str, Any]:
        response = await client.post(
            url,
            json={"application_id": APP_ID, "action": "intent", **payload},
        )
        return await response.json()

    start = await post(intent="StartIntent", session={"retries": 1})
    assert start["speech"].endswith("Was möchtest du wissen?")
    assert start["end_session"] is False
    answer = await post(intent="FrageIntent", text="wer goethe war")
    assert answer["speech"] == "Ein Dichter."
    assert agents.calls[-1]["text"].count("wer goethe war") >= 1
