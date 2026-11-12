"""Tests for the skill code and the voice model of the own Alexa skill."""
from __future__ import annotations

import ast
import json
import re

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
        for sample in intent["samples"]:
            # A free-text slot needs at least one word in front of it
            assert not sample.startswith("{")
            assert re.fullmatch(r"[a-zäöüß ]+( \{frage\})?", sample), sample
            samples.append(sample)
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
