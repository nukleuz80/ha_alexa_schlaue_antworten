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
CONF_PRIMARY_TIMEOUT = "primary_timeout"
CONF_ANSWER_BUDGET = "answer_budget"
CONF_LATE_TEXT = "late_text"
CONF_VOICE_PATH = "voice_path"
CONF_INVOCATION_NAME = "invocation_name"
CONF_SKILL_KEEP_OPEN = "skill_keep_open"
SKILL_OPTION_KEYS = (CONF_INVOCATION_NAME, CONF_SKILL_KEEP_OPEN)

# Default values
DEFAULT_PRIMARY_AGENT = "conversation.google_ai_conversation_2"
DEFAULT_FALLBACK_AGENT = "conversation.google_ai_conversation"
# Seconds after which the fallback agent races the primary one (0 = only on an error)
DEFAULT_PRIMARY_TIMEOUT = 2.5
# Seconds from the question until Alexa must say something (0 = no limit)
DEFAULT_ANSWER_BUDGET = 6.0
VOICE_PATH_COMMUNITY = "community"
VOICE_PATH_SKILL = "skill"
VOICE_PATH_BOTH = "both"
VOICE_PATHS = [VOICE_PATH_COMMUNITY, VOICE_PATH_SKILL, VOICE_PATH_BOTH]
DEFAULT_VOICE_PATH = VOICE_PATH_COMMUNITY
DEFAULT_INVOCATION_NAME = "schlaufuchs"
DEFAULT_SKILL_KEEP_OPEN = False
SKILL_ANOTHER_TEXT = "Noch eine Frage?"
SKILL_ASK_TEXT = "Was möchtest du wissen?"
SKILL_HELP_TEXT = (
    "Frag mich einfach etwas, zum Beispiel: Wie weit ist der Mond entfernt? "
    "Damit ich den Raum kenne, sag mir einmal: Du stehst in der Küche."
)
SKILL_ROOM_SET_TEXT = "Alles klar, ich merke mir: Hier steht {echo}."
SKILL_ROOM_UNKNOWN_TEXT = (
    "Ich finde keinen Echo zu {room}. Du kannst ihn in den Optionen von "
    "Schlaue Antworten unter Echo-Zuordnung auswählen."
)
SKILL_ROOM_NO_DEVICE_TEXT = "Dieses Gerät kann ich leider nicht erkennen."
SKILL_PHONE_NOTHING_TEXT = (
    "Ich habe gerade keine Antwort, die ich aufs Handy schicken kann. "
    "Frag mich zuerst etwas."
)
DEFAULT_LATE_TEXT = "Das dauert gerade zu lange, ich schicke dir die Antwort aufs Handy."
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
    "Ergänze die bisherige Antwort zur Fragestellung '{question}' um die wichtigsten weiteren Informationen "
    "in 2 bis 3 kurzen Sätzen auf Deutsch (höchstens 350 Zeichen) für direkte Sprachausgabe "
    "(keine Aufzählungen oder Sonderzeichen). "
    "Wiederhole den Inhalt nicht. Bereits gegebene Kurzantwort: {previous_answer}"
)
# Earlier defaults; an entry that still holds one of them gets the current default
LEGACY_PROMPTS_DETAILED = (
    "Ergänze die bisherige Antwort zur Fragestellung '{question}' um weitere wichtige Informationen "
    "in 3 bis 4 prägnanten Sätzen auf Deutsch für direkte Sprachausgabe (keine Aufzählungen oder Sonderzeichen). "
    "Wiederhole den Inhalt nicht. Bereits gegebene Kurzantwort: {previous_answer}",
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

# Words inside a question that ask for the answer on the smartphone as well
MOBILE_QUESTION_PHRASES = (
    "aufs handy",
    "auf mein handy",
    "aufs smartphone",
    "aufs telefon",
    "per nachricht",
)
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


# Claude bridge: voice prompts from the own skill into a Claude Code session
CONF_CLAUDE_URL = "claude_url"
CONF_CLAUDE_TOKEN = "claude_token"
CONF_CLAUDE_ECHOS = "claude_echos"
DEFAULT_CLAUDE_URL = ""
DEFAULT_CLAUDE_TOKEN = ""
CLAUDE_SENT_TEXT = "Okay, ist bei Claude. Die Antwort kommt gleich hier."
CLAUDE_SENT_SESSION_TEXT = "Okay, ist bei Claude {session}. Die Antwort kommt gleich hier."
CLAUDE_CREATED_TEXT = "Okay, die Claude-Sitzung {session} startet. Die Antwort kommt gleich hier."
CLAUDE_CREATED_EMPTY_TEXT = (
    "Okay, die Claude-Sitzung {session} läuft. Aufträge gehen jetzt dorthin."
)
CLAUDE_SWITCHED_TEXT = "Okay, Aufträge gehen jetzt an Claude {session}."
CLAUDE_SWITCHED_MAIN_TEXT = "Okay, Aufträge gehen wieder an die Hauptsitzung."
CLAUDE_ENDED_TEXT = "Die Claude-Sitzung {session} ist beendet."
CLAUDE_UNKNOWN_SESSION_TEXT = "Eine Claude-Sitzung {session} gibt es nicht. {running}"
CLAUDE_TOO_MANY_TEXT = (
    "Es laufen schon zu viele Claude-Sitzungen. Beende zuerst eine. {running}"
)
CLAUDE_MAIN_SESSION_TEXT = (
    "Die Hauptsitzung bleibt immer an. Nimm einen anderen Namen."
)
CLAUDE_NO_NAME_TEXT = "Wie soll die Sitzung heißen?"
CLAUDE_RUNNING_TEXT = "Es laufen: {sessions}."
CLAUDE_LIST_TEXT = "Es laufen: {sessions}. Aufträge gehen an {active}."
CLAUDE_MAIN_NAME = "die Hauptsitzung"
CLAUDE_OFF_TEXT = "Die Claude-Brücke ist gerade ausgeschaltet."
CLAUDE_NOT_SET_UP_TEXT = (
    "Die Claude-Brücke ist noch nicht eingerichtet. Das geht in den Optionen "
    "von Schlaue Antworten."
)
CLAUDE_NOT_ALLOWED_TEXT = "Von diesem Echo aus darf ich Claude nichts schicken."
CLAUDE_UNKNOWN_ECHO_TEXT = (
    "Ich weiß noch nicht, welcher Echo das ist. Sag mir zuerst: Du stehst in der "
    "Küche, oder in welchem Raum du gerade bist."
)
CLAUDE_BUSY_TEXT = "Das sind gerade zu viele Aufträge für Claude. Warte bitte kurz."
CLAUDE_UNREACHABLE_TEXT = "Claude ist gerade nicht erreichbar."
CLAUDE_EMPTY_TEXT = "Was soll ich Claude sagen?"
CLAUDE_REST_TEXT = "Den Rest schicke ich dir aufs Handy."
