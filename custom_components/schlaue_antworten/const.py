"""Constants for the Schlaue Antworten integration."""
from __future__ import annotations

DOMAIN = "schlaue_antworten"

# Configuration options
CONF_PRIMARY_AGENT = "primary_agent"
CONF_FALLBACK_AGENT = "fallback_agent"
CONF_DEFAULT_ECHO = "default_echo"
CONF_DIALOG_PROMPT = "dialog_prompt"
CONF_ANNOUNCE_MODEL = "announce_model"
CONF_SHORT_ANSWERS = "short_answers"
CONF_ENABLE_LOGGING = "enable_logging"
CONF_ENABLE_HA_CONTEXT = "enable_ha_context"
CONF_CUSTOM_KNOWLEDGE = "custom_knowledge"
CONF_ENABLE_DETAILED_FOLLOWUP = "enable_detailed_followup"
CONF_FOLLOWUP_PROMPT = "followup_prompt"
CONF_GOODBYE_TEXT = "goodbye_text"
CONF_INTERACTIVE_CONFIRM_PROMPT = "interactive_confirm_prompt"
CONF_NOTIFY_TARGET = "notify_target"
CONF_MOBILE_CONFIRMATION = "mobile_confirmation"
CONF_RETRY_PROMPT = "retry_prompt"
CONF_ABORT_PROMPT = "abort_prompt"
CONF_ENABLE_DIRECT_QUERY = "enable_direct_query"
CONF_DIRECT_QUERY_PREFIXES = "direct_query_prefixes"
CONF_PROMPT_SHORT = "prompt_short"
CONF_PROMPT_DETAILED = "prompt_detailed"

# Default values
DEFAULT_PRIMARY_AGENT = "conversation.google_ai_conversation_2"
DEFAULT_FALLBACK_AGENT = "conversation.google_ai_conversation"
DEFAULT_ECHO = "media_player.wohnzimmer_echo_dot"
DEFAULT_DIALOG_PROMPT = "Schlaue Antworten: Was möchtest du wissen?"
DEFAULT_ANNOUNCE_MODEL = True
DEFAULT_SHORT_ANSWERS = True
DEFAULT_ENABLE_LOGGING = True
DEFAULT_ENABLE_HA_CONTEXT = True
DEFAULT_CUSTOM_KNOWLEDGE = ""
DEFAULT_ENABLE_DETAILED_FOLLOWUP = True
DEFAULT_FOLLOWUP_PROMPT = "Möchtest du eine ausführlichere Erklärung? Ja oder Nein?"
DEFAULT_GOODBYE_TEXT = "Alles klar."
DEFAULT_INTERACTIVE_CONFIRM_PROMPT = "Wird erledigt."
DEFAULT_NOTIFY_TARGET = "notify.notify"
DEFAULT_MOBILE_CONFIRMATION = "Ich habe dir die Antwort aufs Handy geschickt."
DEFAULT_RETRY_PROMPT = "Das habe ich leider nicht verstanden. Bitte wiederhole deine Frage."
DEFAULT_ABORT_PROMPT = "Ich konnte dich leider wieder nicht verstehen. Versuche es bitte später noch einmal."
DEFAULT_ENABLE_DIRECT_QUERY = True
DEFAULT_DIRECT_QUERY_PREFIXES = "schlaue frage, frage ki, ki frage, ki, schlaue antworten"
CODEWORD_UNVERSTAENDLICH = "[UNVERSTAENDLICH]"

FILLER_PHRASES = {
    "ähm",
    "äh",
    "öhm",
    "öh",
    "hm",
    "hmm",
    "hallo",
    "test",
    "warte",
    "warte mal",
    "keine ahnung",
    "was",
    "wer",
    "wie",
    "warum",
    "blabla",
    "blablabla",
}

DEFAULT_PROMPT_SHORT = (
    "Antworte extrem kurz und prägnant in maximal 1 bis 2 Sätzen auf Deutsch (maximal 120 Zeichen) "
    "für direkte Sprachausgabe (ohne Aufzählungen, Formatierungen oder Sonderzeichen). "
    "Berechne Rechenaufgaben direkt. Frage: {question}. "
    "Nur wenn die Eingabe reines unvollständiges Gemurmel ist, antworte ausschließlich mit: [UNVERSTAENDLICH]"
)
DEFAULT_PROMPT_DETAILED = (
    "Ergänze die bisherige Antwort zur Fragestellung '{question}' um weitere wichtige Informationen "
    "in 3 bis 4 prägnanten Sätzen auf Deutsch für direkte Sprachausgabe (keine Aufzählungen oder Sonderzeichen). "
    "Wiederhole den Inhalt nicht. Bereits gegebene Kurzantwort: {previous_answer}"
)

# Events & Services
EVENT_ACTIONABLE_NOTIFICATION = "alexa_actionable_notification"
EVENT_ID_QUERY = "alexa_ki_query"
EVENT_ID_FOLLOWUP = "alexa_ki_followup"
EVENT_ID_INTERACTIVE = "alexa_interactive_question"
EVENT_ACTION_CONFIRMED = "schlaue_antworten_action_confirmed"
EVENT_ACTION_DECLINED = "schlaue_antworten_action_declined"
SERVICE_START_DIALOG = "start_dialog"
SERVICE_ASK_QUESTION = "ask_question"
SERVICE_INTERACTIVE_QUESTION = "interactive_question"

MOBILE_TRIGGER_PHRASES = (
    "handy",
    "smartphone",
    "telefon",
    "nachricht",
    "aufs handy",
    "aufs smartphone",
    "auf mein handy",
    "schick mir",
    "schicken",
    "senden",
    "aufs telefon",
    "push",
)

# Helper entity to listen for existing scene/routine triggers
TRIGGER_BOOLEAN_ENTITY = "input_boolean.alexa_ki_trigger"
ENTITY_ID_ACTIONABLE_INPUT_TEXT = "input_text.alexa_actionable_notification"
DEFAULT_COMMUNITY_SKILL_ID = "amzn1.ask.skill.77bf0c24-791b-4993-9aaa-236298a83d40"

