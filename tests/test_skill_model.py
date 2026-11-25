"""Tests for the skill code and the voice model of the own Alexa skill."""
from __future__ import annotations

import ast
import json
import re
import time
from typing import Any

from custom_components.schlaue_antworten.skill_model import (
    BUILT_IN_INTENTS,
    INTENT_PHONE,
    INTENT_QUESTION,
    QUESTION_WORD_INTENTS,
    SLOT_QUESTION,
    build_skill_code,
    interaction_model_json,
    is_valid_invocation,
    question_from_intent,
)

PLAN_WORDS = (
    "wer", "was", "wie", "wo", "wann", "warum", "wieso", "weshalb",
    "welche", "welcher", "welches",
)


def _model() -> dict:
    return json.loads(interaction_model_json("schlaufuchs"))["interactionModel"][
        "languageModel"
    ]


def test_every_question_word_has_an_intent() -> None:
    """Each planned question word has its own intent with the free-text slot."""
    words = {word for word, _carriers in QUESTION_WORD_INTENTS.values()}
    assert set(PLAN_WORDS) <= words
    intents = {intent["name"]: intent for intent in _model()["intents"]}
    for name in QUESTION_WORD_INTENTS:
        assert intents[name]["slots"] == [
            {"name": SLOT_QUESTION, "type": "AMAZON.SearchQuery"}
        ]


def test_model_is_valid_for_alexa() -> None:
    """Names, samples and slots follow the rules of the developer console."""
    model = _model()
    assert model["invocationName"] == "schlaufuchs"
    names = [intent["name"] for intent in model["intents"]]
    assert len(names) == len(set(names))
    assert set(BUILT_IN_INTENTS) <= set(names)
    assert {INTENT_QUESTION, INTENT_PHONE} <= set(names)
    samples: list[str] = []
    for intent in model["intents"]:
        if not intent["name"].startswith("AMAZON."):
            assert re.fullmatch(r"[A-Za-z]+", intent["name"])
        search_query = any(
            slot["type"] == "AMAZON.SearchQuery" for slot in intent.get("slots", [])
        )
        for sample in intent["samples"]:
            samples.append(sample)
            if not search_query and sample == "{freitext}":
                # A custom slot type may stand alone (the free-text intent)
                continue
            # An AMAZON.SearchQuery slot needs at least one word in front of it
            assert not sample.startswith("{")
            assert re.fullmatch(r"[a-zäöüß ]+( \{frage\})?", sample), sample
    # Alexa: one slot name may have only one type in the whole model
    slot_types: dict[str, str] = {}
    for intent in model["intents"]:
        for slot in intent.get("slots", []):
            assert slot_types.setdefault(slot["name"], slot["type"]) == slot["type"]
    types = {t["name"] for t in model["types"]}
    for intent in model["intents"]:
        for slot in intent.get("slots", []):
            assert slot["type"].startswith("AMAZON.") or slot["type"] in types
    assert len(samples) == len(set(samples))


def test_question_from_intent() -> None:
    """The question word goes back in front of what Alexa understood."""
    assert question_from_intent("WieIntent", "weit ist der mond") == (
        "wie weit ist der mond"
    )
    assert question_from_intent("GibtEsIntent", "leben auf dem mars") == (
        "gibt es leben auf dem mars"
    )
    assert question_from_intent(INTENT_QUESTION, "photosynthese") == "photosynthese"
    assert question_from_intent("WieIntent", "") == ""
    assert question_from_intent("AMAZON.StopIntent", "") is None
    assert question_from_intent(None, "x") is None


def test_skill_code_is_valid_python() -> None:
    """The skill code compiles and contains the address and the time limit."""
    code = build_skill_code("https://example.ui.nabu.casa/api/webhook/abc")
    tree = ast.parse(code)
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "lambda_handler" in functions
    assert 'WEBHOOK_URL = "https://example.ui.nabu.casa/api/webhook/abc"' in code
    assert "TIMEOUT_SECONDS = 6.5" in code
    assert '.get("frage")' in code


def test_invocation_names() -> None:
    """Alexa only accepts lower case letters and spaces."""
    assert is_valid_invocation("schlaufuchs")
    assert is_valid_invocation("schlauer fuchs")
    assert not is_valid_invocation("Schlaufuchs")
    assert not is_valid_invocation("schlau fuchs 2")
    assert not is_valid_invocation("")


def test_invocation_sentences_in_open_dialog() -> None:
    """In an open dialog "frag schlaufuchs ..." and "öffne schlaufuchs" match."""
    intents = {intent["name"]: intent for intent in _model()["intents"]}
    assert "frag schlaufuchs {frage}" in intents[INTENT_QUESTION]["samples"]
    assert "öffne schlaufuchs" in intents["StartIntent"]["samples"]


def _skill_namespace() -> dict[str, Any]:
    """Load the generated skill code like Lambda does."""
    namespace: dict[str, Any] = {}
    exec(build_skill_code("https://example/api/webhook/abc"), namespace)  # noqa: S102
    return namespace


def _intent_event() -> dict[str, Any]:
    return {
        "context": {
            "System": {
                "application": {"applicationId": "app"},
                "device": {"deviceId": "dev"},
                "apiEndpoint": "https://api.amazonalexa.example",
                "apiAccessToken": "tok",
            }
        },
        "request": {
            "type": "IntentRequest",
            "requestId": "req-1",
            "intent": {"name": INTENT_QUESTION, "slots": {}},
        },
    }


def test_progress_text_only_when_slow() -> None:
    """A slow answer gets "Moment." first, a fast one does not."""
    namespace = _skill_namespace()
    namespace["PROGRESS_AFTER_SECONDS"] = 0.05
    sent: list[dict[str, Any]] = []
    namespace["_send_progress"] = lambda event: sent.append(event)
    delay = {"seconds": 0.0}

    def fake_call(event: dict[str, Any], *args: Any) -> dict[str, Any]:
        time.sleep(delay["seconds"])
        return namespace["_response"]("Antwort")

    namespace["_call_home_assistant"] = fake_call

    answer = namespace["lambda_handler"](_intent_event(), None)
    assert answer["response"]["outputSpeech"]["text"] == "Antwort"
    assert not sent

    delay["seconds"] = 0.2
    answer = namespace["lambda_handler"](_intent_event(), None)
    assert answer["response"]["outputSpeech"]["text"] == "Antwort"
    assert len(sent) == 1


def test_progress_directive(monkeypatch: Any) -> None:
    """The progress text goes to the Alexa directives API with the request id."""
    namespace = _skill_namespace()
    calls: list[Any] = []

    class _Reply:
        def close(self) -> None:
            pass

    def fake_urlopen(request: Any, timeout: float) -> _Reply:
        calls.append((request.full_url, json.loads(request.data), request.headers))
        return _Reply()

    monkeypatch.setattr(namespace["urllib"].request, "urlopen", fake_urlopen)
    namespace["_send_progress"](_intent_event())
    url, body, headers = calls[0]
    assert url == "https://api.amazonalexa.example/v1/directives"
    assert body["header"]["requestId"] == "req-1"
    assert body["directive"] == {"type": "VoicePlayer.Speak", "speech": "Moment."}
    assert headers["Authorization"] == "Bearer tok"

    # An empty text turns it off
    namespace["PROGRESS_TEXT"] = ""
    namespace["_send_progress"](_intent_event())
    assert len(calls) == 1


def test_card_only_on_a_screen() -> None:
    """The APL card goes only to Echos that support APL."""
    namespace = _skill_namespace()
    card = {"title": "Frage", "text": "Antwort", "footer": "Beantwortet von KI"}
    event = _intent_event()
    assert namespace["_card_directive"](event, card) is None

    event["context"]["System"]["device"]["supportedInterfaces"] = {
        "Alexa.Presentation.APL": {"runtime": {"maxVersion": "2023.3"}}
    }
    directive = namespace["_card_directive"](event, card)
    assert directive["type"] == "Alexa.Presentation.APL.RenderDocument"
    assert directive["datasources"] == {"card": card}
    assert namespace["_card_directive"](event, None) is None
    json.dumps(directive)  # Alexa gets it as JSON

    answer = namespace["_response"]("Antwort", directive=directive)
    assert answer["response"]["directives"] == [directive]
