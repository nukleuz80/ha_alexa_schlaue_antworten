"""Tests for the answer core that every voice path shares."""
from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.schlaue_antworten.answer import (
    OVERLOADED_TEXT,
    is_error_reply,
    is_unclear_reply,
)
from custom_components.schlaue_antworten.const import (
    DEFAULT_PROMPT_SHORT,
    DOMAIN,
    LEGACY_PROMPTS_SHORT,
)

from .conftest import ECHO, FakeAgents, SetupEntry
from .test_init import FALLBACK, OPTIONS, PRIMARY


def test_error_and_unclear_detection() -> None:
    """Empty and error replies count as errors, marked replies as unclear."""
    assert is_error_reply(None)
    assert is_error_reply("")
    assert is_error_reply("Error talking to API")
    assert not is_error_reply("Der Mond ist weit weg.")
    assert is_unclear_reply("[UNVERSTÄNDLICH]")
    assert is_unclear_reply("Unverständlich, bitte wiederholen.")
    assert not is_unclear_reply("Goethe war ein Dichter.")


async def test_answer_with_model_name(
    hass: HomeAssistant, setup_entry: SetupEntry, agents: FakeAgents
) -> None:
    """The spoken text names the model, the plain text does not."""
    entry = await setup_entry({**OPTIONS, "announce_model": True})
    agents.answers[PRIMARY] = "Goethe war ein *Dichter*."
    hass.states.async_set(PRIMARY, "ok", {"friendly_name": "Testmodell"})

    result = await hass.data[DOMAIN][entry.entry_id].answers.async_answer(
        "Wer war Goethe?", ECHO
    )
    assert result.text == "Goethe war ein Dichter."
    assert result.speech == "Goethe war ein Dichter. Beantwortet von Testmodell."
    assert result.agent == PRIMARY
    assert not result.error
    assert PRIMARY in result.agent_seconds


async def test_unclear_answer(
    hass: HomeAssistant, setup_entry: SetupEntry, agents: FakeAgents
) -> None:
    """A question the AI did not understand is reported as unclear."""
    entry = await setup_entry(OPTIONS)
    agents.answers[PRIMARY] = "[UNVERSTÄNDLICH]"
    engine = hass.data[DOMAIN][entry.entry_id].answers

    result = await engine.async_answer("blub", ECHO)
    assert result.unclear
    # A follow-up is never treated as unclear
    result = await engine.async_answer("blub", ECHO, is_followup=True)
    assert not result.unclear


async def test_overloaded_answer(
    hass: HomeAssistant, setup_entry: SetupEntry, agents: FakeAgents
) -> None:
    """Both agents failing gives the overloaded text."""
    entry = await setup_entry(OPTIONS)
    agents.answers[PRIMARY] = RuntimeError("down")
    agents.answers[FALLBACK] = "rate limit"
    result = await hass.data[DOMAIN][entry.entry_id].answers.async_answer("x?", ECHO)
    assert result.error
    assert result.speech == OVERLOADED_TEXT
    assert set(result.agent_seconds) == {PRIMARY, FALLBACK}


async def test_prompts(hass: HomeAssistant, setup_entry: SetupEntry) -> None:
    """Short and detailed templates take the question and the previous answer."""
    entry = await setup_entry(
        {
            **OPTIONS,
            "short_answers": True,
            "prompt_short": "Kurz: {question}",
            "prompt_detailed": "Lang: [question] (bisher: {previous_answer})",
        }
    )
    engine = hass.data[DOMAIN][entry.entry_id].answers
    assert engine.build_prompt("Wer war Goethe?", ECHO) == "Kurz: Wer war Goethe?"
    assert (
        engine.build_prompt("Wer war Goethe?", ECHO, True, "Ein Dichter.")
        == "Lang: Wer war Goethe? (bisher: Ein Dichter.)"
    )


async def test_context_in_prompt(hass: HomeAssistant, setup_entry: SetupEntry) -> None:
    """With context enabled the prompt carries room, weather, people and wiki."""
    entry = await setup_entry(
        {
            **OPTIONS,
            "short_answers": False,
            "enable_ha_context": True,
            "custom_knowledge": "Gast-WLAN: blume\nMüll: Dienstag",
        }
    )
    hass.states.async_set("weather.home", "sunny", {"temperature": 12})
    hass.states.async_set("person.jan", "home", {"friendly_name": "Jan"})
    engine = hass.data[DOMAIN][entry.entry_id].answers
    prompt = engine.build_prompt("Wetter? Wer ist zu Hause?", ECHO)
    assert prompt.startswith(
        "Wetter? Wer ist zu Hause? [Smart-Home-Kontext: Zeitpunkt: "
    )
    assert "Standort: Test Echo" in prompt
    assert "Wetter: sonnig, 12°C" in prompt
    assert "Zu Hause: Jan" in prompt
    assert "Haus-Fakten: Gast-WLAN: blume | Müll: Dienstag" in prompt


async def test_context_only_when_needed(
    hass: HomeAssistant, setup_entry: SetupEntry
) -> None:
    """Weather and presence come along only when the question needs them."""
    entry = await setup_entry(
        {**OPTIONS, "short_answers": False, "enable_ha_context": True}
    )
    hass.states.async_set("weather.home", "sunny", {"temperature": 12})
    hass.states.async_set("person.jan", "home", {"friendly_name": "Jan"})
    engine = hass.data[DOMAIN][entry.entry_id].answers

    prompt = engine.build_prompt("Wer war Goethe?", ECHO)
    assert "Zeitpunkt: " in prompt
    assert "Standort: Test Echo" in prompt
    assert "Wetter:" not in prompt
    assert "Zu Hause:" not in prompt

    prompt = engine.build_prompt("Brauche ich heute eine Jacke?", ECHO)
    assert "Wetter: sonnig, 12°C" in prompt
    assert "Zu Hause:" not in prompt

    prompt = engine.build_prompt("Ist jemand daheim?", ECHO)
    assert "Zu Hause: Jan" in prompt
    assert "Wetter:" not in prompt

    # A follow-up gets the whole context
    prompt = engine.build_prompt("Wer war Goethe?", ECHO, True, "Ein Dichter.")
    assert "Wetter: sonnig, 12°C" in prompt
    assert "Zu Hause: Jan" in prompt


async def test_legacy_short_prompt_gets_new_default(
    hass: HomeAssistant, setup_entry: SetupEntry
) -> None:
    """An entry that still holds an old default short prompt uses the new one."""
    entry = await setup_entry(
        {**OPTIONS, "short_answers": True, "prompt_short": LEGACY_PROMPTS_SHORT[1]}
    )
    prompt = hass.data[DOMAIN][entry.entry_id].answers.build_prompt("Wie hoch?", ECHO)
    assert prompt.startswith(
        DEFAULT_PROMPT_SHORT.replace("{question}", "Wie hoch?")[:40]
    )
    assert "Wie hoch?" in prompt
