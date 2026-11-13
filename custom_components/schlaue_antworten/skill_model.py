"""Skill code and voice model for the own Alexa skill.

The skill code is kept small on purpose: it hands every request to Home
Assistant, so later improvements arrive with the integration and the code in
the Alexa developer console rarely needs to be replaced.
"""
from __future__ import annotations

import json
import re
from typing import Any

SKILL_LOCALE = "de-DE"
SLOT_QUESTION = "frage"
INTENT_QUESTION = "FrageIntent"
INTENT_PHONE = "HandyIntent"
INTENT_START = "StartIntent"

# Alexa's free-text slot needs a word in front of it. Each question word gets
# its own intent, so Home Assistant can put the word back in front of the slot.
QUESTION_WORD_INTENTS: dict[str, tuple[str, list[str]]] = {
    "WerIntent": ("wer", ["wer"]),
    "WasIntent": ("was", ["was"]),
    "WieIntent": ("wie", ["wie"]),
    "WoIntent": ("wo", ["wo"]),
    "WannIntent": ("wann", ["wann"]),
    "WarumIntent": ("warum", ["warum"]),
    "WiesoIntent": ("wieso", ["wieso"]),
    "WeshalbIntent": ("weshalb", ["weshalb"]),
    "WelcheIntent": ("welche", ["welche"]),
    "WelcherIntent": ("welcher", ["welcher"]),
    "WelchesIntent": ("welches", ["welches"]),
    "WelchenIntent": ("welchen", ["welchen"]),
    "WoherIntent": ("woher", ["woher"]),
    "WohinIntent": ("wohin", ["wohin"]),
    "WozuIntent": ("wozu", ["wozu"]),
    "WomitIntent": ("womit", ["womit"]),
    "WovonIntent": ("wovon", ["wovon"]),
    "IstIntent": ("ist", ["ist"]),
    "SindIntent": ("sind", ["sind"]),
    "KannIntent": ("kann", ["kann", "kannst du mir sagen"]),
    "GibtEsIntent": ("gibt es", ["gibt es"]),
    "HatIntent": ("hat", ["hat"]),
    "ErklaerIntent": ("erkläre mir", ["erklär mir", "erkläre mir", "erkläre"]),
    "ErzaehlIntent": ("erzähl mir", ["erzähl mir", "erzähle mir"]),
    "NenneIntent": ("nenne mir", ["nenne mir", "nenn mir"]),
    "UebersetzeIntent": ("übersetze", ["übersetze", "übersetz"]),
}
# Carrier phrases whose words carry no meaning; the slot alone is the question
QUESTION_CARRIERS = [
    "frage",
    "ich habe eine frage",
    "ich möchte wissen",
    "ich will wissen",
    "sag mir",
    "weißt du",
]
PHONE_SAMPLES = [
    "schick es aufs handy",
    "schick es mir aufs handy",
    "schick das aufs handy",
    "schick mir die antwort aufs handy",
    "aufs handy bitte",
    "schick mir das aufs handy",
    "aufs handy",
    "sende es an mein handy",
    "schick die antwort aufs handy",
]
BUILT_IN_INTENTS = [
    "AMAZON.YesIntent",
    "AMAZON.NoIntent",
    "AMAZON.StopIntent",
    "AMAZON.CancelIntent",
    "AMAZON.HelpIntent",
    "AMAZON.FallbackIntent",
    "AMAZON.NavigateHomeIntent",
]

RE_INVOCATION = re.compile(r"^[a-zäöüß]+( [a-zäöüß]+)*$")

SKILL_CODE_TEMPLATE = '''"""Schlaue Antworten Alexa skill. Keep this code private, it contains your secret address."""
import json
import urllib.error
import urllib.request

WEBHOOK_URL = "__WEBHOOK_URL__"
# Amazon waits about 8 seconds; Home Assistant answers within 6
TIMEOUT_SECONDS = 6.5
UNREACHABLE = "Home Assistant ist gerade nicht erreichbar. Versuch es bitte gleich noch einmal."
INACTIVE = "Der eigene Skill ist in Schlaue Antworten gerade nicht eingeschaltet."


def _response(text, end_session=True, reprompt=None, session=None):
    answer = {
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "PlainText", "text": text},
            "shouldEndSession": end_session,
        },
    }
    if reprompt and not end_session:
        answer["response"]["reprompt"] = {
            "outputSpeech": {"type": "PlainText", "text": reprompt}
        }
    if session:
        answer["sessionAttributes"] = session
    return answer


def _call_home_assistant(event, action, intent=None, text=""):
    system = event["context"]["System"]
    payload = {
        "application_id": system["application"]["applicationId"],
        "device_id": system.get("device", {}).get("deviceId"),
        "action": action,
        "intent": intent,
        "text": text,
        "session": (event.get("session") or {}).get("attributes") or {},
        "locale": event["request"].get("locale"),
    }
    request = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as reply:
            body = reply.read().decode()
            data = json.loads(body) if body else {}
    except (urllib.error.URLError, TimeoutError, ValueError):
        return _response(UNREACHABLE)
    if not data.get("speech"):
        return _response(INACTIVE)
    return _response(
        data["speech"],
        data.get("end_session", True),
        data.get("reprompt"),
        data.get("session"),
    )


def lambda_handler(event, context):
    request = event["request"]
    if request["type"] == "LaunchRequest":
        return _call_home_assistant(event, "launch")
    if request["type"] != "IntentRequest":
        if request.get("error"):
            print(json.dumps(request["error"]))
        return {"version": "1.0", "response": {}}
    intent = request.get("intent", {})
    slot = (intent.get("slots") or {}).get("__SLOT__") or {}
    return _call_home_assistant(event, "intent", intent.get("name"), slot.get("value") or "")
'''.replace("__SLOT__", SLOT_QUESTION)


def build_skill_code(webhook_url: str) -> str:
    """Return the skill code with the secret address filled in."""
    return SKILL_CODE_TEMPLATE.replace("__WEBHOOK_URL__", webhook_url)


def is_valid_invocation(name: str) -> bool:
    """Return whether Alexa accepts the name: lower case letters and spaces."""
    return bool(RE_INVOCATION.match(name))


def question_from_intent(intent: str | None, value: str) -> str | None:
    """Return the full question for a question intent, or None for other intents."""
    if intent == INTENT_QUESTION:
        return value
    if intent in QUESTION_WORD_INTENTS:
        word = QUESTION_WORD_INTENTS[intent][0]
        return f"{word} {value}".strip() if value else ""
    return None


def _question_slot() -> list[dict[str, str]]:
    return [{"name": SLOT_QUESTION, "type": "AMAZON.SearchQuery"}]


def build_interaction_model(invocation: str) -> dict[str, Any]:
    """Return the voice model for the Alexa developer console."""
    intents: list[dict[str, Any]] = [
        {"name": name, "samples": []} for name in BUILT_IN_INTENTS
    ]
    for name, (_word, carriers) in QUESTION_WORD_INTENTS.items():
        intents.append(
            {
                "name": name,
                "slots": _question_slot(),
                "samples": [f"{carrier} {{{SLOT_QUESTION}}}" for carrier in carriers],
            }
        )
    # In an open dialog Alexa matches a new "frag schlaufuchs ..." against this
    # skill's sentences, so the invocation itself has to be one of them
    carriers = [*QUESTION_CARRIERS, f"frag {invocation}", f"frage {invocation}"]
    intents.append(
        {
            "name": INTENT_QUESTION,
            "slots": _question_slot(),
            "samples": [f"{carrier} {{{SLOT_QUESTION}}}" for carrier in carriers],
        }
    )
    intents.append({"name": INTENT_PHONE, "samples": list(PHONE_SAMPLES)})
    intents.append(
        {
            "name": INTENT_START,
            "samples": [f"öffne {invocation}", f"starte {invocation}"],
        }
    )
    return {
        "interactionModel": {
            "languageModel": {
                "invocationName": invocation,
                "intents": intents,
                "types": [],
            }
        }
    }


def interaction_model_json(invocation: str) -> str:
    """Return the voice model as text to paste into the JSON editor."""
    return json.dumps(build_interaction_model(invocation), indent=2, ensure_ascii=False)
