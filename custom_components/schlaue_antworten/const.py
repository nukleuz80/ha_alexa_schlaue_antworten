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
CONF_ENABLE_DETAILED_FOLLOWUP = "enable_detailed_followup"
CONF_FOLLOWUP_PROMPT = "followup_prompt"
CONF_GOODBYE_TEXT = "goodbye_text"
CONF_PROMPT_SHORT = "prompt_short"
CONF_PROMPT_DETAILED = "prompt_detailed"

# Default values
DEFAULT_PRIMARY_AGENT = "conversation.google_ai_conversation_2"
DEFAULT_FALLBACK_AGENT = "conversation.google_ai_conversation"
DEFAULT_ECHO = "media_player.wohnzimmer_echo_dot"
DEFAULT_DIALOG_PROMPT = "Schlaue Antworten: Was möchtest du wissen?"
DEFAULT_ANNOUNCE_MODEL = True
DEFAULT_SHORT_ANSWERS = True
DEFAULT_ENABLE_DETAILED_FOLLOWUP = False
DEFAULT_FOLLOWUP_PROMPT = "Möchtest du eine ausführlichere Erklärung? Ja oder Nein?"
DEFAULT_GOODBYE_TEXT = "Alles klar."
DEFAULT_PROMPT_SHORT = (
    "Bitte antworte kurz und prägnant in maximal 1 bis 2 Sätzen auf Deutsch "
    "für eine direkte Sprachausgabe ohne Aufzählungen, ohne Listen, "
    "ohne Formatierungen und ohne Sonderzeichen auf folgende Frage: {question}"
)
DEFAULT_PROMPT_DETAILED = (
    "Ergänze die bisherige Antwort zur Fragestellung '{question}' um weitere wichtige Informationen, "
    "interessante Hintergründe und Details in etwa 3 bis 5 Sätzen auf Deutsch für eine direkte Sprachausgabe "
    "ohne Aufzählungen, ohne Listen und ohne Sonderzeichen. "
    "Wiederhole den bereits genannten Inhalt nicht noch einmal, sondern liefere neue wichtige Aspekte. "
    "Bereits gegebene Kurzantwort: {previous_answer}"
)

# Events & Services
EVENT_ACTIONABLE_NOTIFICATION = "alexa_actionable_notification"
EVENT_ID_QUERY = "alexa_ki_query"
EVENT_ID_FOLLOWUP = "alexa_ki_followup"
SERVICE_START_DIALOG = "start_dialog"
SERVICE_ASK_QUESTION = "ask_question"

# Helper entity to listen for existing scene/routine triggers
TRIGGER_BOOLEAN_ENTITY = "input_boolean.alexa_ki_trigger"

