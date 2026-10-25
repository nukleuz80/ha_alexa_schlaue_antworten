<p align="center">
  <img src="www/schlaue_antworten/logo.png" alt="Schlaue Antworten Logo" width="180">
</p>

<h1 align="center">ALEXA - Schlaue Antworten</h1>
<p align="center"><b>KI-Sprachdialog für Amazon Alexa &amp; Home Assistant</b></p>

<p align="center">
  <a href="https://github.com/nukleuz80/ha_alexa_schlaue_antworten/releases"><img src="https://img.shields.io/badge/version-1.0.26-blue.svg" alt="Version"></a>
  <a href="https://www.home-assistant.io/"><img src="https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg" alt="Home Assistant"></a>
  <a href="https://hacs.xyz/"><img src="https://img.shields.io/badge/HACS-Custom%20Repository-orange.svg" alt="HACS"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
</p>

**Schlaue Antworten** verbindet deine Amazon Echo-Lautsprecher nahtlos mit modernen KI-Sprachmodellen (z. B. Google Gemini, Anthropic Claude, OpenAI oder lokalen LLMs) in Home Assistant.

Du hast die Wahl zwischen zwei komfortablen Sprachwegen:
- ⚡ **Ein-Satz-Direktabfrage:** *„Alexa, schlaue Frage: Wie weit ist der Mond entfernt?“* (Direkte Antwort in einem Rutsch)
- 🗣️ **Interaktiver Dialog:** *„Alexa, öffne Schlaue Antworten“* ➔ *„Schlaue Antworten: Was möchtest du wissen?“* (Offenes Mikrofon mit blauem Leuchtring)

---

## 🔒 100 % Privat, Lokal & Zero-YAML – Kein Entwicklerkonto nötig!

Im Gegensatz zu vielen herkömmlichen Alexa-Custom-Skill-Lösungen:
- ❌ **Kein** Amazon Developer Account erforderlich
- ❌ **Keine** AWS-Lambda-Funktionen oder Cloud-Proxies
- ❌ **Kein YAML-Code nötig:** Keine manuellen Skripte (`scripts.yaml`), keine Helfer (`input_text`, `input_boolean`) und keine Template-Sensoren
- ❌ **Keine** sensiblen URLs, Tokens oder Zugangsdaten, die irgendwo extern eingetragen werden müssen
- ✅ **100 % isoliert:** Alle Dialoge, KI-Abfragen und Antworten verbleiben vollständig in deiner eigenen Home-Assistant-Instanz.

---

## ✨ Features

- 📊 **Nativer Statistik-Sensor (Tageszähler ab v1.0.26):** Stellt `sensor.alexa_schlaue_antworten_ki_anfragen_heute` bereit; zählt alle KI-Anfragen des aktuellen Tages, setzt sich um Mitternacht automatisch auf 0 zurück, speichert Daten persistent im HA-Speicher (`.storage`) und liefert nützliche Attribute (Kurz- vs. Lang-Antworten, Gesamtzahl, letztes Echo, Zeitstempel & Dauer).
- ⚡ **Native Ein-Satz-Direktabfrage (ab v1.0.24):** Stelle deine Frage direkt in einem Satz (*„Alexa, schlaue Frage: ...“* oder *„Alexa, frage KI: ...“*), ohne dass zuvor eine Zwischenfrage abgewartet werden muss – 100 % nativ ohne YAML-Automationen!
- 🚀 **100 % Zero-YAML Setup (ab v1.0.23):** Vollständige Integration out-of-the-box ohne YAML-Konfiguration.
- 🔘 **Native Schalter- & Taster-Entitäten:** Stellt `switch.alexa_schlaue_antworten_dialog_starten` bereit, der direkt in Alexa-Routinen geschaltet werden kann, sowie einen praktischen Button für Dashboards.
- 🗣️ **Interaktiver Sprachdialog:** Startet mit *„Schlaue Antworten: Was möchtest du wissen?“* und lässt das Mikrofon offen für deine Frage.
- 🎯 **Dynamische Raum-Erkennung:** Erkennt automatisch das aktive Echo-Gerät anhand des `last_called`-Status der `alexa_media`-Geräte (oder optional via `sensor.last_alexa`).
- 📜 **Kompaktes Dialog-Log:** Protokolliert die letzten Interaktionen (Gerät, Input, Output, Latenz und Zeichenanzahl) direkt in den Optionen.
- 🔄 **2-Stufen-Fehlererkennung mit Schleifenschutz:** Fängt Gemurmel oder unverständliche Fragen ab, bittet einmalig höflich um Wiederholung und beendet bei erneutem Fehlschlag geräuschlos den Dialog.
- 💬 **Optionale Vertiefung (Follow-up):** Fragt nach der Kurzantwort automatisch nach (*„Möchtest du mehr darüber erfahren?“*). Sagst du *„Ja“*, liefert die KI eine ausführlichere Erklärung (3–5 Sätze), ohne die Kurzantwort zu wiederholen.
- ⚡ **Blitzschnelle Antwortzeiten:** Optimiert für kompakte Sprachausgaben (1–2 prägnante Sätze) in ca. 1–2 Sekunden.
- 🛡️ **Intelligenter Ausweich-Mechanismus (Fallback):** Fängt Serverüberlastungen (wie Google 503 High Demand) automatisch ab und wechselt unterbrechungsfrei auf deinen Ausweich-Agenten (z. B. Claude Sonnet).
- 🏠 **Smart-Home-Kontext im Prompt:** Übergibt optional Wetter, Außentemperatur, genaue Uhrzeit/Wochentag, den aktuellen Raum sowie die Anwesenheit an die KI (z. B. für Fragen wie *„Brauche ich heute einen Schirm?“* oder *„Wie spät ist es?“*).
- 📖 **Haus-Wiki & Familien-Fakten:** Erlaubt es, in den Einstellungen individuelle Notizen zu hinterlegen (z. B. WLAN-Gastpasswort, Müllabfuhr-Tage, Haustiernamen, Notfallnummern), auf die die KI bei Haushaltsfragen zugreift.
- 🚨 **Proaktive Fragen für Automatisierungen:** Dienst `schlaue_antworten.interactive_question` stellt bei Ereignissen eine Ja/Nein-Frage über Alexa und feuert bei *„Ja“* bzw. *„Nein“* entsprechende Events (`schlaue_antworten_action_confirmed`/`declined`).
- 📱 **Auf mein Handy senden:** Sage im Dialog *„Aufs Handy senden“* oder frage direkt *„... und schick es mir aufs Smartphone“*, um die Antwort als Push-Mitteilung an die Home Assistant Companion App zu erhalten.
- 🧹 **Perfekt für die Sprachausgabe aufbereitet:** Bereinigt automatisch störende Markdown-Sterne (`*`), Rauten (`#`) und Sonderzeichen.
- 🏷️ **Transparente Modellnennung:** Nennt auf Wunsch am Ende der Antwort automatisch das Modell (*„Beantwortet von Google Gemini.“*).
- ⚙️ **Vollständige UI-Konfiguration:** Alle Modelle, Prompts und Standardwerte werden direkt in der Benutzeroberfläche verwaltet.

---

## 📋 Schnellstart (Zero-YAML)

In nur 3 einfachen Schritten ist *Schlaue Antworten* einsatzbereit:

### 1. Voraussetzungen in Home Assistant
1. **Alexa Media Player (HACS):** Muss installiert und eingerichtet sein (wird für Sprachausgabe und Echo-Erkennung benötigt).
2. **Community-Skill aktivieren:** Aktiviere in deinem Amazon-Konto den kostenlosen Actionable-Notification-Skill mit der ID:  
   `amzn1.ask.skill.77bf0c24-791b-4993-9aaa-236298a83d40`  
   *(Kein Developer-Account und keine Lambda-Konfiguration nötig!)*
3. **Ein KI-Agent:** Mindestens eine aktive Sprach-KI-Integration in Home Assistant:
   - 💡 **OpenRouter (⭐ Unsere Empfehlung für den Einstieg):**  
     Nutze OpenRouter mit kostenlosen Modellen (z. B. `meta-llama/llama-3.3-70b-instruct:free` oder `openrouter/free`).  
     *Keine Kreditkarte, keine Vorabkosten, keine Monatsgebühren – sofort startklar!*
   - Alternativ: Google Generative AI (Gemini), Anthropic Claude, OpenAI oder lokale LLMs (z. B. Ollama).

---

### 2. Integration installieren & einrichten
1. Installiere **Schlaue Antworten** über HACS (Custom Repository) oder manuell.
2. Gehe in Home Assistant auf **Einstellungen ➔ Geräte & Dienste ➔ + Integration hinzufügen** und wähle **Schlaue Antworten**.
3. Wähle deinen primären KI-Agenten und dein Standard-Echo-Gerät aus.

---

### 3. Alexa-Routine erstellen (für interaktiven Dialog)
Erstelle in der Alexa-Smartphone-App eine neue Routine:
- **Wenn Folgendes passiert (Stimme):** `öffne schlaue antworten`
- **Aktion hinzufügen (Smart Home ➔ Geräte):** Schalter **`Schlaue Antworten: Dialog starten`** auf **AN** stellen.

*Fertig! Sobald du „Alexa, öffne Schlaue Antworten“ sagst, leuchtet dein Echo blau und erwartet deine Frage. Für Ein-Satz-Fragen („Alexa, schlaue Frage: ...“) ist nicht einmal eine Routine nötig!*

---

<details>
<summary>📦 <b>Für bestehende Setups / Legacy-YAML-Modus (Klick zum Ausklappen)</b></summary>

Falls du bereits ein bestehendes Setup aus früheren Versionen nutzt, bleibt alles zu **100 % abwärtskompatibel**:
- Die Integration prüft weiterhin automatisch, ob `sensor.last_alexa`, `input_boolean.alexa_ki_trigger` oder `script.activate_alexa_actionable_notification` existieren, und nutzt diese bevorzugt.
- Du musst bestehende Skripte, Helfer oder Szenen nicht löschen – sie funktionieren nahtlos weiter.
</details>

---

## ⚙️ Konfiguration (UI Options Flow)

Klicke in **Einstellungen ➔ Geräte & Dienste** bei **Schlaue Antworten** auf **Konfigurieren**:

- **Primärer KI-Agent:** Hauptmodell für Antworten (z. B. Google Gemini 2 oder OpenRouter Llama 3.3).
- **Ausweich-Agent (Fallback):** Modell, das bei 503-Überlastung automatisch einspringt (z. B. Claude Sonnet).
- **Standard-Echo:** Fallback-Gerät, falls der aktive Echo einmal nicht eindeutig ermittelt werden kann.
- **Begrüßungsansage:** Der Starttext für den Dialog (Standard: *„Schlaue Antworten: Was möchtest du wissen?“*).
- **Modellname am Ende der Antwort ansagen:** Hängt z. B. *„Beantwortet von Google Gemini.“* an (Tipp: Deaktivieren spart ~1,5s Sprechzeit).
- **Kurze Antworten für Sprache erzwingen:** Begrenzt die Antwortlänge auf 1–2 gesprochene Sätze.
- **Direktabfrage in einem Satz aktivieren:** Erlaubt direkte Fragen wie *„Alexa, schlaue Frage: ...“* (Standard: *aktiviert*).
- **Signalwörter für Direktabfrage:** Kommagetrennte Trigger-Wörter (Standard: `schlaue frage, frage ki, ki frage, ki, schlaue antworten`).
- **Dialog-Log aktivieren:** Schaltet die Protokollierung der letzten Dialoge an/aus.
- **Smart-Home-Kontext an KI übergeben:** Schaltet die Übergabe von Wetter, Uhrzeit, Echo-Standort und Anwesenheit an die KI an/aus.
- **Haus-Wiki & Familien-Fakten:** Mehrzeiliges Notizfeld für individuelles Haushaltswissen (z. B. WLAN-Passwort für Gäste, Müllabfuhrtermine, Notfallnummern).
- **Ziel-Gerät für Smartphone-Push:** Benachrichtigungsdienst für Antworten ans Handy (z. B. `notify.notify` oder `notify.mobile_app_...`).
- **Sprachbestätigung beim Senden aufs Smartphone:** Was Alexa sagen soll (Standard: *„Ich habe dir die Antwort aufs Handy geschickt.“*).
- **Bestätigungsansage bei Automatisierungs-Freigabe ('Ja'):** Text, wenn eine interaktive Automatisierungsfrage mit *„Ja“* beantwortet wird (Standard: *„Wird erledigt.“*).
- **Ausführlichere Vertiefung anbieten (Follow-up):** Fragt nach jeder Antwort, ob du mehr erfahren möchtest (Standard: *aktiviert*).
- **Fragetext für Vertiefung:** Eigener Text für die Nachfrage (Standard: *„Möchtest du eine ausführlichere Erklärung? Ja oder Nein?“*).
- **Abschiedstext bei Ablehnung ('Nein'):** Kurze Verabschiedung bei Ablehnung (Standard: *„Alles klar.“*).
- **Wiederholungsansage bei unverständlicher Frage:** Text für den ersten Fehlversuch (Standard: *„Das habe ich leider nicht verstanden. Bitte wiederhole deine Frage.“*).
- **Abbruchansage nach zweitem Fehlversuch:** Beendet den Dialog bei wiederholt unverständlicher Eingabe (Standard: *„Ich konnte dich leider wieder nicht verstehen. Versuche es bitte später noch einmal.“*).
- **KI-Prompts für Kurzantwort & Vertiefung:** Frei anpassbare System-Prompts mit Platzhaltern `{question}` und `{previous_answer}`.

---

## 🗣️ Ablauf im Alltag

### ⚡ Variante 1: Direktabfrage in einem Satz (Neu)
1. **Du sagst:**  
   > *„Alexa, schlaue Frage: Wie weit ist der Mond entfernt?“*  
   *(oder „Alexa, frage KI: ...“ bzw. „Alexa, KI: ...“)*
2. **Alexa antwortet direkt nach ca. 2 Sekunden** mit der Antwort der KI – ohne Zwischenfrage!
3. **Vertiefungs-Modus:** Alexa fragt im Anschluss: *„Möchtest du eine ausführlichere Erklärung? Ja oder Nein?“*.

### 💬 Variante 2: Klassischer interaktiver Dialog
1. **Du sagst:**  
   > *„Alexa, öffne Schlaue Antworten“*
2. **Dein Echo leuchtet blau und fragt:**  
   > *„Schlaue Antworten: Was möchtest du wissen?“*
3. **Du stellst frei heraus deine Frage:**  
   - *„Was kann ich heute mit Kartoffeln und Spinat kochen?“*
   - *„Erkläre mir die Relativitätstheorie in zwei Sätzen.“*
   - *„Wie lautet das WLAN-Passwort für Gäste?“*
4. **Alexa antwortet und bietet Vertiefung an.**

---

## ⚡ Performance- & Latenz-Tipps

1. 🔇 **Modellansage deaktivieren:** Spart ca. 1,5 Sekunden reine Sprechzeit pro Antwort.
2. 🏎️ **Smarte Musik-Vorprüfung:** Läuft keine Musik, wird kein blockierender Cloud-Stop-Befehl gesendet (spart 1–2 Sekunden beim Dialogstart).
3. 🤖 **Websuche in OpenRouter ausschalten:** In OpenRouter `web_search: off` stellen, um Suchmaschinen-Wartezeiten zu vermeiden (Antwort in 1–2 Sekunden).

---

## 🛠️ Dienste (Services)

| Dienst | Beschreibung | Parameter |
| :--- | :--- | :--- |
| `schlaue_antworten.start_dialog` | Startet den interaktiven Frage-Dialog auf einem Echo. | `echo_device` *(optional)* |
| `schlaue_antworten.ask_question` | Sendet eine Frage direkt an die KI und gibt das Ergebnis aus. | `question` *(erforderlich)*, `echo_device` *(optional)* |
| `schlaue_antworten.interactive_question` | Stellt eine Ja/Nein-Rückfrage über Alexa und feuert Events für Folge-Automatisierungen. | `question` *(erforderlich)*, `echo_device` *(optional)*, `event_id` *(optional)* |

### 💡 Beispiel: Proaktive Automatisierungs-Rückfrage

```yaml
# 1. Automatisierung: Alexa stellt die Frage mit geöffnetem Mikrofon
action: schlaue_antworten.interactive_question
data:
  question: "Die Waschmaschine ist fertig. Soll ich die Steckdose ausschalten?"
  event_id: waschmaschine_fertig

# 2. Folge-Automatisierung: Reagiert auf "Ja"
trigger:
  - trigger: event
    event_type: schlaue_antworten_action_confirmed
    event_data:
      event_id: waschmaschine_fertig
action:
  - action: switch.turn_off
    target:
      entity_id: switch.steckdose_waschmaschine
```

---

## 📜 Versionshistorie & Changelog

| Version | Datum | Highlights |
| :--- | :--- | :--- |
| **v1.0.26** | 25.10.2026 | **Nativer Statistik-Sensor (Tageszähler):** 1) Neue Sensor-Entität `sensor.alexa_schlaue_antworten_ki_anfragen_heute` (bzw. `_queries_today`); zählt alle KI-Anfragen des aktuellen Tages mit automatischer Rücksetzung um Mitternacht (`00:00:00`); 2) Persistente Speicherung via Home Assistant `Store` (übersteht Neustarts ohne Datenverlust); 3) Detaillierte Attribute (`anfragen_heute`, `kurze_antworten_heute`, `ausfuehrliche_antworten_heute`, `anfragen_gesamt`, `letzte_anfrage`, `letztes_echo`, `letzte_uhrzeit`, `letzte_dauer_sekunden`). |
| **v1.0.25** | 25.10.2026 | **Echo-Geräteauflösung & Sofort-Stopp für native Suchantworten:** 1) Präzise Zuordnung des auslösenden Echo-Lautsprechers aus `alexa_media_last_called_event` über die Hardware-Seriennummer (`last_called` ➔ `entity_registry.unique_id`) sowie Friendly Name; verhindert Fehlleitungen auf das Standardgerät; 2) Bedingungsloser Sofort-Stopp (`media_player.media_stop`) auf dem Ziel-Echo, um Alexas native Websuch-Monologe (*„Hier ist eine Antwort von Qucka / Übersetzt von answers.com“*) unmittelbar zu unterbrechen, bevor die KI-Antwort gesprochen wird. |
| **v1.0.24** | 25.10.2026 | **Native Ein-Satz-Direktabfrage (One-Sentence Voice Query):** 1) Fragen können nun direkt in einem einzigen Satz gesprochen werden (*„Alexa, schlaue Frage: ...“*, *„Alexa, frage KI: ...“* oder *„Alexa, KI: ...“*); 2) 100 % nativ in der Integration über `alexa_media_last_called_event` ohne manuelle YAML-Automationen; 3) Vollständig konfigurierbar in der UI (Ein/Aus-Schalter und anpassbare Signalwörter); 4) Intelligenter Kollisionsschutz mit bestehenden Routinen (*„öffne schlaue antworten“*) und Brainstorm-Befehlen. |
| **v1.0.23** | 24.10.2026 | **Zero-YAML Revolution & Native Entitäten:** 1) 100 % YAML-freie Installation – kein manuelles Anlegen von `input_text`, `scripts.yaml`, `scenes.yaml` oder Template-Sensoren mehr erforderlich; 2) Neue native Entitäten `switch.alexa_schlaue_antworten_dialog_starten` (Schalter für Alexa-Routinen) und `button.alexa_schlaue_antworten_dialog_starten` (Taster für Dashboards/Automatisierungen); 3) Automatische Erkennung des aktiven Echo-Lautsprechers direkt aus dem `last_called`-Status der `media_player`-Entitäten in Python; 4) Direkte Skill-Ausführung via Python; 5) 100 % abwärtskompatibel zu bestehenden YAML-Setups. |
| **v1.0.22** | 24.10.2026 | Neue Features: 1) Proaktiver Dialog-Dienst `schlaue_antworten.interactive_question` für Automatisierungen (Alexa stellt bei Ereignissen eine Ja/Nein-Rückfrage und feuert `schlaue_antworten_action_confirmed` bzw. `declined` Events); 2) Push-Notification aufs Smartphone ('Auf mein Handy senden') per Sprachbefehl im Dialog oder direkt in der Frage. |
| **v1.0.21** | 24.10.2026 | Neues Feature: Haus-Wiki & Familien-Fakten (mehrzeiliges Eingabefeld in den Einstellungen für individuelles Haushaltswissen wie WLAN-Gastpasswörter, Müllabfuhr-Termine oder Haustiernamen; wird als Teil des Smart-Home-Kontexts an die KI übergeben und ermöglicht präzise Auskünfte zu persönlichen Haushaltsfragen). |
| **v1.0.20** | 24.10.2026 | Neues Feature: Smart-Home-Kontext im Prompt (Wetter, Außentemperatur, genaue Uhrzeit/Wochentag, Echo-Standort/Raum und Anwesenheit werden als kompakter Kontextblock diskret an das KI-Modell übergeben – ermöglicht orts- und wetterbezogene Fragen wie 'Brauche ich einen Schirm?', 'Wie spät ist es?' oder 'Wer ist zu Hause?'); ein-/ausschaltbar in den Einstellungen. |
| **v1.0.19** | 24.10.2026 | Performance- & Latenz-Update: 1-2 Sekunden Zeitersparnis beim Dialogstart durch smarte Zustandsprüfung (kein unnötiger Cloud-Stop-Call bei inaktiver Musikwiedergabe; nicht-blockierende Ausführung); gestraffter Kurzantwort-Prompt für schnellere Time-To-First-Token; vorab kompilierte Regex-Muster und $O(1)$-Set-Lookups; Non-Blocking-TTS; Dokumentationsabschnitt zu Performance- und Latenztipps (u. a. Einsparung von 1,5s durch Deaktivieren der Modellansage). |
| **v1.0.18** | 24.10.2026 | Dokumentations-Erweiterung: Detaillierte Empfehlung für OpenRouter mit kostenlosen Modellen (z. B. Llama 3.3 70B Free / Gemini Flash Free) für einen schnellen, risikofreien Einstieg ohne monatliche Fixkosten oder Kreditkarte aufgenommen. |
| **v1.0.17** | 24.10.2026 | Critical Bugfix: Endlosschleife beim Speichern der Einstellungen (`update_listener`) behoben; anstelle rekursiver manueller Reload-Aufrufe nutzt die Integration nun das native `hass.config_entries.async_reload`, wodurch das 4096-Websocket-Nachrichtenlimit, Browser-Abbrüche („disconnected“) und Endlos-Spinner beim Speichern dauerhaft beseitigt wurden. |
| **v1.0.16** | 24.10.2026 | Follow-up-Erweiterung & Puffer-Handling: 255-Zeichen-Limitierung von `input_text.alexa_actionable_notification` behoben (längere Antworten werden zuerst über TTS ausgegeben, gefolgt von der Nachfrage mit geöffnetem Mikrofon); Standardwert für Vertiefungs-Nachfrage auf `Aktiviert` geändert. |
| **v1.0.15** | 24.10.2026 | Rechenaufgaben-Erkennung & Logging-Option: Mathematische Berechnungen (z. B. `33/11`, `5*8`, `100-25`) werden nun explizit als gültig erkannt und nicht mehr fälschlicherweise als unvollständige Eingabe abgewiesen; neue Einstellung `Dialog-Log aktivieren` (An/Aus-Schalter) zur flexiblen Aktivierung/Deaktivierung der Protokollierung hinzugefügt. |
| **v1.0.14** | 24.10.2026 | Logo- & Icon-Optimierung: Gehirn und Sprechblasen-Glow im Verhältnis zur Gesamtkachelfläche deutlich vergrößert (Füllrate von ~55 % auf über 90 % der Breite angehoben, dunkle Randbereiche minimiert) für optimale Erkennbarkeit auf kleinen Displays und Kacheln. |
| **v1.0.13** | 24.10.2026 | Separater Dialog für Dialog-Log & FormatJS-Endfix: Dialog-Log vollständig aus den Einstellungen ausgelagert und in ein eigenes Menüfenster (`📜 Dialog-Log`) überführt; Einstellungen (`⚙️ Einstellungen & Prompts`) als eigenständiger Menüschritt ohne Textvariablen strukturiert (verhindert jegliche FormatJS-Fehler); automatische Entleerung des Translations-Caches beim Neuladen der Integration. |
| **v1.0.12** | 24.10.2026 | FormatJS-Bugfix & OptionsFlow-Standardisierung: Frontend-Fehler 'MISSING_VALUE: question' behoben (Platzhalter in Übersetzungstexten klammerneutral als `[question]` und `[previous_answer]` formatiert); `OptionsFlow`-Klasse auf modernen parameterlosen Standard refaktoriert (verhindert 500 Server Error beim Aufruf); Brand-Icons als valide PNG-Dateien neu generiert. |
| **v1.0.11** | 23.10.2026 | Bugfix & Brand-Assets: 500-Fehler beim Laden des Options Flows behoben (Property-Konflikt in `config_flow.py` gelöst); offizielle Brand-Icons (`icon.png`, `logo.png` und `brand/`-Ordner) direkt im Integrationsverzeichnis hinterlegt, sodass Home Assistant das Logo in „Geräte & Dienste“ anzeigt. |
| **v1.0.10** | 23.10.2026 | Log-Erweiterung: Messung der Latenz / Antwortdauer (vom Ende der Spracheingabe bis zum Start der Sprachausgabe) sowie Anzeige der genauen Zeichenanzahl bei kurzen und langen Antworten (z. B. `Kurz • 142 Z. • 1.3s`). |
| **v1.0.9** | 23.10.2026 | Kompaktes Dialog-Log direkt in den Integration-Optionen: Protokolliert die letzten Interaktionen mit Uhrzeit, angesprochenem Echo-Lautsprecher, Eingabe und Ausgabe (auf max. 100 Zeichen begrenzt). |
| **v1.0.8** | 23.10.2026 | 2-Stufen-Erkennung für unverständliche Fragen (lokaler Filter + KI-Semantikprüfung) mit Schleifenschutz (Loop Protection): Bittet beim ersten Mal höflich um Wiederholung mit erneut geöffnetem Mikrofon und beendet nach dem zweiten Fehlversuch sauber den Dialog. Vollständig konfigurierbar. |
| **v1.0.7** | 23.10.2026 | Kontextbewusste Vertiefung: Übergabe der bereits gesprochenen Kurzantwort an die KI via `{previous_answer}`-Platzhalter. Verhindert 1:1-Wiederholungen und priorisiert neue, weiterführende Informationen zur Frage. |
| **v1.0.6** | 23.10.2026 | Frei konfigurierbare KI-System-Prompts für kurze und ausführliche Antworten direkt in den Integration-Optionen (mit `{question}`-Platzhalter, Hinweistext „ohne Gewähr“ und mehrzeiligen Texteingabefeldern). |
| **v1.0.5** | 23.10.2026 | Ja/Nein-Entscheidungsführung für Vertiefungsfragen (*„Möchtest du eine ausführlichere Erklärung? Ja oder Nein?“*). Bei „Nein“ beendet Alexa den Dialog sofort mit einem konfigurierbaren, minimalen Abschiedstext (Standard: *„Alles klar.“*). |
| **v1.0.4** | 23.10.2026 | Neues Feature: Optionale interaktive Vertiefungsfrage (Follow-up) nach jeder Antwort (*„Möchtest du mehr darüber erfahren?“*). Antwortet der Nutzer positiv, liefert die KI eine vertiefende 3–5-Satz-Erklärung. Vollständig über die UI konfigurierbar (Standard: deaktiviert). |
| **v1.0.3** | 23.10.2026 | Umfassende Dokumentationsüberarbeitung: Klarstellung der privaten Architektur (kein AWS Lambda / kein Entwicklerkonto nötig), Schritt-für-Schritt-Anleitung und Alltags-Beispiele. |
| **v1.0.2** | 23.10.2026 | Bild-Assets in dedizierten Ordner `www/schlaue_antworten/` verschoben und Pfade/Skripte bereinigt. |
| **v1.0.1** | 23.10.2026 | Offizielles Logo hinzugefügt (SVG- und PNG-Assets) und Dokumentations-Update. |
| **v1.0.0** | 23.10.2026 | Erstveröffentlichung als native Custom Integration mit vollständigem Options Flow, dynamischer Raum-Erkennung via `sensor.last_alexa`, 503-Ausweich-Logik (Fallback) und nahtloser Alexa Actionable Notifications Anbindung. |

---

## 📄 Lizenz
MIT License. Siehe [`LICENSE`](LICENSE) für Details.
