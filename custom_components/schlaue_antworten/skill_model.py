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
INTENT_ROOM = "RaumIntent"
INTENT_THIS_PHONE = "MeinHandyIntent"
# Catches any sentence without a known start, e.g. the task after "Claude soll"
INTENT_FREE = "FreitextIntent"
FREE_SLOT_TYPE = "FREITEXT"
# Alexa allows one type per slot name, so the free text slot has its own name
SLOT_FREE = "freitext"
# Varied sample values teach Alexa to take whole sentences as the slot value
FREE_SAMPLE_VALUES = [
    "prüf die fenster",
    "schau nach ob alle türen zu sind",
    "mach das licht im büro aus",
    "wie warm ist es im wohnzimmer",
    "erstelle eine automation die abends die rollläden schließt",
    "ja",
    "nein",
    "alle übernehmen",
    "nur den ersten vorschlag",
    "repariere das dashboard",
    "warum ist der sensor nicht erreichbar",
    "lies mir die letzten fehler im log vor",
    "schreib eine notiz einkaufen milch und brot",
    "starte die waschmaschine um acht",
    "welche geräte verbrauchen gerade viel strom",
    "ein bild reparieren",
    "fasse zusammen was heute passiert ist",
    "erinnere mich morgen an den müll",
    "heizung im bad auf zweiundzwanzig grad",
    "mach weiter",
    "zeig mir den plan",
    "ändere die farbe der karte auf blau",
    "kannst du das rückgängig machen",
    "teste die neue version",
    "was hast du gerade gemacht",
]
INTENT_CLAUDE = "ClaudeIntent"
INTENT_CLAUDE_NEW = "ClaudeNeuIntent"
INTENT_CLAUDE_SWITCH = "ClaudeWechselIntent"
INTENT_CLAUDE_LIST = "ClaudeListeIntent"
INTENT_CLAUDE_END = "ClaudeEndeIntent"

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
# "Du stehst in der Küche": tells which Echo this is. The slot keeps the name
# "frage", so the skill code needs no change
ROOM_CARRIERS = [
    "du stehst in",
    "du stehst im",
    "du stehst in der",
    "dieser echo steht in",
    "dieser echo steht im",
    "dieser echo steht in der",
    "ich bin in",
    "ich bin im",
    "ich bin in der",
]
# How Alexa writes down "Claude" (it often hears "cloud" or "coth")
CLAUDE_SPELLINGS = ["claude", "cloud", "clod", "klod", "kloth", "coth", "clode"]


def _with_spellings(samples: list[str]) -> list[str]:
    """Repeat every sample with each spelling of "Claude", without duplicates."""
    result: list[str] = []
    for sample in samples:
        for spelling in CLAUDE_SPELLINGS:
            variant = sample.replace("claude", spelling)
            if variant not in result:
                result.append(variant)
    return result


# "Claude soll ...": the prompt goes to the Claude bridge, not to the AI answer
CLAUDE_CARRIERS = [
    "claude soll",
    "sag claude",
    "frag claude",
    "an claude",
    "schick claude",
    "auftrag an claude",
    "claude bitte",
    "antworte claude",
    "antwort an claude",
    "antwort für claude",
]


def claude_task(question: str) -> str | None:
    """Return the task of "Claude soll ..." that Alexa took for a question.

    Alexa sometimes hands the whole sentence to the catch-all intent, and it
    would otherwise go to the AI answer instead of the Claude bridge.
    """
    words = re.sub(r"[^\w\s]", " ", question.casefold()).split()
    spoken = " ".join(words)
    for carrier in sorted(_with_spellings(CLAUDE_CARRIERS), key=len, reverse=True):
        if spoken.startswith(carrier + " "):
            task = spoken[len(carrier) :].strip()
            return task if len(task) >= 2 else None
    return None


# "neue Claude-Sitzung Heizung prüf das Bad": first word is the name
CLAUDE_NEW_CARRIERS = [
    "neue claude sitzung",
    "starte claude sitzung",
    "starte eine claude sitzung",
    "neue sitzung",
    "öffne claude sitzung",
]
CLAUDE_SWITCH_CARRIERS = [
    "wechsle zu claude",
    "wechsel zu claude",
    "wechsle zur claude sitzung",
    "wechsle zu sitzung",
    "nimm claude sitzung",
    "zurück zu claude",
]
CLAUDE_END_CARRIERS = [
    "beende claude",
    "beende claude sitzung",
    "beende die claude sitzung",
    "schließe claude sitzung",
    "stoppe claude sitzung",
]
CLAUDE_LIST_SAMPLES = [
    "welche claude sitzungen laufen",
    "welche sitzungen laufen",
    "liste die claude sitzungen",
    "welche claude sitzung ist aktiv",
    "zeig die claude sitzungen",
]
# Said in the Alexa app on the phone: this device is the phone, not an Echo
THIS_PHONE_SAMPLES = [
    "das ist mein handy",
    "du bist mein handy",
    "ich bin am handy",
    "ich spreche über die app",
    "das ist die alexa app",
    "ich bin in der alexa app",
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
import threading
import urllib.error
import urllib.request

WEBHOOK_URL = "__WEBHOOK_URL__"
# Amazon waits about 8 seconds; Home Assistant answers within 6
TIMEOUT_SECONDS = 6.5
UNREACHABLE = "Home Assistant ist gerade nicht erreichbar. Versuch es bitte gleich noch einmal."
INACTIVE = "Der eigene Skill ist in Schlaue Antworten gerade nicht eingeschaltet."
# Said while Home Assistant still thinks; an empty text turns it off
PROGRESS_TEXT = "Moment."
PROGRESS_AFTER_SECONDS = 1.0


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


def _send_progress(event):
    """Let Alexa say PROGRESS_TEXT now, before the real answer is ready."""
    system = event["context"]["System"]
    endpoint = system.get("apiEndpoint")
    token = system.get("apiAccessToken")
    if not (PROGRESS_TEXT and endpoint and token):
        return
    body = {
        "header": {"requestId": event["request"]["requestId"]},
        "directive": {"type": "VoicePlayer.Speak", "speech": PROGRESS_TEXT},
    }
    request = urllib.request.Request(
        endpoint + "/v1/directives",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(request, timeout=1.0).close()
    except (urllib.error.URLError, TimeoutError, ValueError) as err:
        print("Progressive response failed: " + str(err))


def _call_with_progress(event, *args):
    """Call Home Assistant; say PROGRESS_TEXT if the answer takes a while."""
    result = {}
    worker = threading.Thread(
        target=lambda: result.update(answer=_call_home_assistant(event, *args))
    )
    worker.start()
    worker.join(PROGRESS_AFTER_SECONDS)
    if worker.is_alive():
        _send_progress(event)
        worker.join()
    return result.get("answer") or _response(UNREACHABLE)


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
    slots = intent.get("slots") or {}
    slot = slots.get("__SLOT__") or slots.get("__FREE__") or {}
    return _call_with_progress(
        event, "intent", intent.get("name"), slot.get("value") or ""
    )
'''.replace("__SLOT__", SLOT_QUESTION).replace("__FREE__", SLOT_FREE)


def build_skill_code(webhook_url: str) -> str:
    """Return the skill code with the secret address filled in."""
    return SKILL_CODE_TEMPLATE.replace("__WEBHOOK_URL__", webhook_url)


def is_valid_invocation(name: str) -> bool:
    """Return whether Alexa accepts the name: lower case letters and spaces."""
    return bool(RE_INVOCATION.match(name))


def question_from_intent(intent: str | None, value: str) -> str | None:
    """Return the full question for a question intent, or None for other intents."""
    if intent in (INTENT_QUESTION, INTENT_FREE):
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
    intents.append(
        {
            "name": INTENT_FREE,
            "slots": [{"name": SLOT_FREE, "type": FREE_SLOT_TYPE}],
            "samples": [f"{{{SLOT_FREE}}}"],
        }
    )
    intents.append({"name": INTENT_PHONE, "samples": list(PHONE_SAMPLES)})
    intents.append({"name": INTENT_THIS_PHONE, "samples": list(THIS_PHONE_SAMPLES)})
    intents.append(
        {
            "name": INTENT_ROOM,
            "slots": _question_slot(),
            "samples": [f"{carrier} {{{SLOT_QUESTION}}}" for carrier in ROOM_CARRIERS],
        }
    )
    intents.append(
        {
            "name": INTENT_CLAUDE,
            "slots": _question_slot(),
            # Bare "Claude soll" asks for the task, so it is not cut off
            "samples": [
                f"{carrier} {{{SLOT_QUESTION}}}"
                for carrier in _with_spellings(CLAUDE_CARRIERS)
            ]
            + _with_spellings(CLAUDE_CARRIERS),
        }
    )
    for name, session_carriers in (
        (INTENT_CLAUDE_NEW, CLAUDE_NEW_CARRIERS),
        (INTENT_CLAUDE_SWITCH, CLAUDE_SWITCH_CARRIERS),
        (INTENT_CLAUDE_END, CLAUDE_END_CARRIERS),
    ):
        intents.append(
            {
                "name": name,
                "slots": _question_slot(),
                "samples": [
                    f"{carrier} {{{SLOT_QUESTION}}}"
                    for carrier in _with_spellings(session_carriers)
                ],
            }
        )
    intents.append(
        {"name": INTENT_CLAUDE_LIST, "samples": _with_spellings(CLAUDE_LIST_SAMPLES)}
    )
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
                "types": [
                    {
                        "name": FREE_SLOT_TYPE,
                        "values": [
                            {"name": {"value": value}} for value in FREE_SAMPLE_VALUES
                        ],
                    }
                ],
            }
        }
    }


def interaction_model_json(invocation: str) -> str:
    """Return the voice model as text to paste into the JSON editor."""
    return json.dumps(build_interaction_model(invocation), indent=2, ensure_ascii=False)
