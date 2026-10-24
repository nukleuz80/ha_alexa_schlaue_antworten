<p align="center">
  <img src="www/schlaue_antworten/logo.png" alt="Schlaue Antworten Logo" width="180">
</p>

<h1 align="center">ALEXA - Schlaue Antworten</h1>
<p align="center"><b>KI-Sprachdialog für Amazon Alexa &amp; Home Assistant</b></p>

<p align="center">
  <a href="https://github.com/nukleuz80/ha_alexa_schlaue_antworten/releases"><img src="https://img.shields.io/badge/version-1.0.19-blue.svg" alt="Version"></a>
  <a href="https://www.home-assistant.io/"><img src="https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg" alt="Home Assistant"></a>
  <a href="https://hacs.xyz/"><img src="https://img.shields.io/badge/HACS-Custom%20Repository-orange.svg" alt="HACS"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
</p>

**Schlaue Antworten** verbindet deine Amazon Echo-Lautsprecher nahtlos mit modernen KI-Sprachmodellen (z. B. Google Gemini, Anthropic Claude oder lokalen LLMs) in Home Assistant.

Per Sprachbefehl **„Alexa, öffne Schlaue Antworten“** meldet sich Alexa mit einem geöffneten Mikrofon (blauer Leuchtring) auf genau dem Echo, vor dem du gerade stehst, nimmt deine freie Wissens- oder Alltagsfrage entgegen und liest dir die Antwort des KI-Modells sekundenschnell und sauber formuliert vor.

---

## 🔒 100 % Privat & Lokal – Kein AWS Lambda oder Entwicklerkonto nötig!

Im Gegensatz zu vielen herkömmlichen Alexa-Custom-Skill-Lösungen:
- ❌ **Kein** Amazon Developer Account erforderlich
- ❌ **Keine** AWS-Lambda-Funktionen oder Cloud-Proxies
- ❌ **Keine** sensiblen URLs, Tokens oder Zugangsdaten, die irgendwo extern eingetragen werden müssen
- ✅ **100 % isoliert:** Alle Dialoge, KI-Abfragen und Antworten verbleiben vollständig in deiner eigenen Home-Assistant-Instanz.

---

## ✨ Features

- 🗣️ **Interaktiver Sprachdialog:** Startet mit *„Schlaue Antworten: Was möchtest du wissen?“* und lässt das Mikrofon offen für deine Frage.
- 📜 **Kompaktes Dialog-Log:** Protokolliert die letzten Interaktionen (welches Echo-Gerät, welcher Input, welcher Output bis 100 Zeichen) direkt sichtbar in den Einstellungen.
- 🔄 **2-Stufen-Fehlererkennung mit Schleifenschutz:** Fängt Gemurmel, Füllwörter oder unverständliche Fragen ab, bittet einmalig höflich um Wiederholung und beendet bei erneutem Fehlschlag geräuschlos den Dialog.
- 💬 **Optionale Vertiefung (Follow-up):** Fragt auf Wunsch nach der Kurzantwort automatisch nach (*„Möchtest du mehr darüber erfahren?“*). Sagst du *„Ja“*, liefert die KI eine ausführlichere Erklärung (3–5 Sätze).
- 🎯 **Dynamische Raum-Erkennung:** Antwortet dank `sensor.last_alexa` automatisch auf dem Echo-Gerät, mit dem du gerade gesprochen hast.
- ⚡ **Blitzschnelle Antwortzeiten:** Optimiert für kompakte Sprachausgaben (1–2 prägnante Sätze) in ca. 1–2 Sekunden.
- 🛡️ **Intelligenter Ausweich-Mechanismus (Fallback):** Fängt Serverüberlastungen (wie Google 503 High Demand) automatisch ab und wechselt unterbrechungsfrei auf deinen konfigurierten Ausweich-Agenten (z. B. Claude Sonnet).
- 🧹 **Perfekt für die Sprachausgabe aufbereitet:** Bereinigt automatisch störende Markdown-Sterne (`*`), Rauten (`#`) und Sonderzeichen.
- 🏷️ **Transparente Modellnennung:** Nennt auf Wunsch am Ende der Antwort automatisch das Modell (*„Beantwortet von Google Gemini.“*).
- ⚙️ **Vollständige UI-Konfiguration:** Alle Modelle, Prompts und Standardwerte können direkt in der Home Assistant Benutzeroberfläche ohne YAML konfiguriert werden.

---

## 📋 Voraussetzungen in Home Assistant

Damit die Integration auf deinen Echo-Geräten funktioniert, müssen die folgenden 5 Bausteine in deinem Home Assistant vorhanden sein:

### 1. Alexa Media Player (HACS)
Wird für die Sprachausgabe (`notify.alexa_media`) und das Stoppen laufender Medien benötigt.
- **Installation:** Über HACS nach *Alexa Media Player* suchen und installieren.

### 2. Alexa Actionable Notifications (Dialog-Pipeline)
Ermöglicht es dem Echo, eine Frage zu stellen und das Mikrofon mit dem blauen Leuchtring für deine Antwort offen zu halten.
- **Skill:** Der offizielle, kostenlose Community-Skill `amzn1.ask.skill.77bf0c24-791b-4993-9aaa-236298a83d40` muss in deinem Amazon-Konto aktiviert sein.
- **Helfer in `configuration.yaml`:**
  ```yaml
  input_text:
    alexa_actionable_notification:
      name: Alexa Actionable Notification
  ```
- **Skript in `scripts.yaml`:**
  ```yaml
  activate_alexa_actionable_notification:
    alias: activate_alexa_actionable_notification
    sequence:
      - action: input_text.set_value
        data:
          entity_id: input_text.alexa_actionable_notification
          value: '{"text": "{{ text }}", "event": "{{ event_id }}", "suppress_confirmation": "{{ suppress_confirmation }}"}'
      - action: media_player.play_media
        data:
          entity_id: "{{ alexa_device }}"
          media_content_type: skill
          media_content_id: amzn1.ask.skill.77bf0c24-791b-4993-9aaa-236298a83d40
  ```

### 3. Sensor für das aktive Echo-Gerät (`sensor.last_alexa`)
Ermittelt automatisch das Echo-Gerät, das den letzten Sprachbefehl empfangen hat:
```yaml
template:
  - sensor:
      - name: "Last Alexa"
        state: >
          {{ expand(integration_entities('alexa_media') | select('search', 'media_player'))
             | selectattr('attributes.last_called', 'defined')
             | selectattr('attributes.last_called', 'eq', true)
             | map(attribute='entity_id') | first | default('media_player.wohnzimmer_echo_dot') }}
```

### 4. Trigger-Helfer & Szene für die Alexa-Routine
Verbindet den Sprachbefehl mit Home Assistant:
- **Helfer (`configuration.yaml`):**
  ```yaml
  input_boolean:
    alexa_ki_trigger:
      name: "Alexa KI Trigger"
      icon: mdi:robot
  ```
- **Szene (`scenes.yaml`):**
  ```yaml
  - id: 'alexa_ki_scene'
    name: 'Schlaue Antworten'
    icon: mdi:robot
    entities:
      input_boolean.alexa_ki_trigger:
        state: 'on'
  ```
- **Routine in der Alexa-Smartphone-App:**
  - **Wenn Folgendes passiert (Stimme):** `öffne schlaue antworten`
  - **Aktion hinzufügen (Smart Home ➔ Szenen):** `Schlaue Antworten`

### 5. Mindestens ein aktiver KI-Agent (Conversation Entity)
Mindestens eine Sprach-KI-Integration muss in Home Assistant aktiv sein:
- 💡 **OpenRouter (⭐ Unsere Empfehlung für den Einstieg):**  
  Wir empfehlen für einen einfachen und unkomplizierten Einstieg **OpenRouter** mit einem der **kostenlosen Modelle** (wie z. B. `meta-llama/llama-3.3-70b-instruct:free`, `google/gemini-2.0-flash-exp:free` o. ä.).  
  - **Vorteil:** Du kannst *Schlaue Antworten* sofort unverbindlich ausprobieren – **ohne Kreditkarte, ohne Vorabkosten und ohne feste Monatsgebühren**.  
  - **Einbindung in Home Assistant:** Über die integrierte *OpenAI Conversation*-Integration (als Basis-URL `https://openrouter.ai/api/v1` und deinen kostenlosen OpenRouter-API-Key angeben) oder die HACS OpenRouter-Integration. Schnelle Reaktionszeiten und hervorragende Antwortqualität garantiert!
- **Google Generative AI (Gemini):** z. B. eine reine Text-Instanz ohne Smart-Home-Entitätssteuerung für maximale Geschwindigkeit (~1,2s Antwortzeit).
- **Anthropic Claude:** z. B. `conversation.anthropic_claude_sonnet_4` für höchste sprachliche Präzision.
- **OpenAI / Local LLM / Ollama:** Beliebige `conversation.*`-Entität oder lokale LLMs für 100 % lokalen Offline-Betrieb.

---

## 🚀 Installation

### Über HACS (Custom Repository)
1. Öffne **HACS** in Home Assistant.
2. Klicke oben rechts auf die drei Punkte ➔ **Benutzerdefinierte Repositories**.
3. URL eintragen: `https://github.com/nukleuz80/ha_alexa_schlaue_antworten`
4. Kategorie: **Integration**.
5. Klicke auf **Hinzufügen** und installiere **Schlaue Antworten**.
6. Starte Home Assistant neu.

### Manuelle Installation
1. Lade das Repository herunter.
2. Kopiere den Ordner `custom_components/schlaue_antworten/` in dein Verzeichnis `/config/custom_components/`.
3. Kopiere den Ordner `www/schlaue_antworten/` in dein Verzeichnis `/config/www/`.
4. Starte Home Assistant neu.

---

## ⚙️ Konfiguration (UI Options Flow)

1. Gehe in Home Assistant auf **Einstellungen ➔ Geräte & Dienste**.
2. Klicke auf **+ Integration hinzufügen** und wähle **Schlaue Antworten**.
3. Klicke nach der Installation auf **Konfigurieren**:
   - **Primärer KI-Agent:** Hauptmodell für Antworten (z. B. Google Gemini 2).
   - **Ausweich-Agent (Fallback):** Modell, das bei 503-Überlastung automatisch einspringt (z. B. Claude Sonnet).
   - **Standard-Echo:** Fallback-Gerät, falls `sensor.last_alexa` einmal nicht gesetzt sein sollte.
   - **Begrüßungsansage:** Der Starttext für den Dialog (Standard: *„Schlaue Antworten: Was möchtest du wissen?“*).
   - **Modellname am Ende der Antwort ansagen:** Hängt z. B. *„Beantwortet von Google Gemini.“* an.
   - **Kurze Antworten für Sprache erzwingen:** Begrenzt die Antwortlänge auf 1–2 gesprochene Sätze.
   - **Ausführlichere Vertiefung anbieten (Follow-up):** Fragt nach jeder Antwort, ob du mehr erfahren möchtest (Standard: *deaktiviert*).
   - **Fragetext für Vertiefung:** Eigener Text für die Nachfrage (Standard: *„Möchtest du eine ausführlichere Erklärung? Ja oder Nein?“*).
   - **Abschiedstext bei Ablehnung ('Nein'):** Kurze Verabschiedung, falls du ablehnst (Standard: *„Alles klar.“*).
   - **Wiederholungsansage bei unverständlicher Frage:** Text für den ersten Fehlversuch (Standard: *„Das habe ich leider nicht verstanden. Bitte wiederhole deine Frage.“*).
   - **Abbruchansage nach zweitem Fehlversuch:** Beendet den Dialog bei wiederholt unverständlicher Eingabe (Standard: *„Ich konnte dich leider wieder nicht verstehen. Versuche es bitte später noch einmal.“*).
   - **KI-Prompt für Kurzantwort (ohne Gewähr):** Mehrzeiliges Eingabefeld für den System-Prompt der Erstantwort. Der Platzhalter `{question}` wird automatisch mit der Frage belegt.
   - **KI-Prompt für Vertiefung (ohne Gewähr):** Mehrzeiliges Eingabefeld für die ausführlichere Erklärung. Unterstützt `{question}` sowie `{previous_answer}` – verhindert Wiederholungen der Kurzantwort und priorisiert gezielt neue Hintergrundinformationen.

---

## 🗣️ Ablauf im Alltag

1. **Du sagst:**  
   > *„Alexa, öffne Schlaue Antworten“*
2. **Dein Echo leuchtet blau und fragt:**  
   > *„Schlaue Antworten: Was möchtest du wissen?“*
3. **Du stellst frei heraus deine Frage:**  
   - *„Wie weit ist der Mond entfernt?“*
   - *„Warum ist der Himmel blau?“*
   - *„Was kann ich heute mit Kartoffeln und Spinat kochen?“*
   - *„Erkläre mir die Relativitätstheorie in zwei Sätzen.“*
4. **Bei unverständlicher Spracheingabe (Schleifenschutz):**  
   Versteht Alexa nur Füllwörter oder Gemurmel, antwortet sie: *„Das habe ich leider nicht verstanden. Bitte wiederhole deine Frage.“* und öffnet das Mikrofon erneut. Bei einem zweiten Fehlversuch verabschiedet sie sich sauber und beendet den Dialog.
5. **Alexa liest dir die prägnante Antwort vor:**  
   *(Optional mit Modellnennung am Ende)*
6. **Vertiefungs-Modus (falls aktiviert):**  
   Alexa fragt direkt im Anschluss: *„Möchtest du eine ausführlichere Erklärung? Ja oder Nein?“* und hält das Mikrofon offen.  
   - Sagst du **„Ja“** (oder *„gerne“*, *„erzähl mir mehr“*), liefert die KI eine weiterführende 3–5-Satz-Erklärung – **ohne die bereits gehörte Kurzantwort zu wiederholen**, sondern mit neuen wichtigen Aspekten und Hintergründen.  
   - Sagst du **„Nein“** (oder *„nein danke“*, *„stopp“*), antwortet Alexa mit einem minimalen Abschiedstext (*„Alles klar.“*) und beendet den Dialog sofort.  
   - Schweigst du, schließt sich das Mikrofon nach dem Timeout geräuschlos.

---

## ⚡ Performance- & Latenz-Optimierung (Jede Sekunde sparen)

Um die Verzögerung zwischen deiner Frage und Alexas Antwort auf ein absolutes Minimum zu reduzieren, beachte folgende Tipps und Neuerungen:

1. 🔇 **Modellansage deaktivieren (Spart ca. 1,5 Sekunden reine Sprechzeit!):**  
   In den Einstellungen der Integration findest du die Option **„Modellname am Ende der Antwort ansagen“**.  
   *Ist diese Option deaktiviert*, liest Alexa ausschließlich die Antwort vor – der Zusatz *„Beantwortet von Google Gemini.“* entfällt. Das spart bei jedem Dialog sofort ca. 1,5 Sekunden Sprechzeit und hält die Gesamtlänge kompakt genug, sodass die Antwort und eine eventuelle Nachfrage nahtlos in einem Rutsch gesprochen werden können.
2. 🏎️ **Smarte Musik-Vorprüfung (ab v1.0.19):**  
   Vor dem Start des Dialogs prüft die Integration im lokalen Zustandscache, ob der Echo überhaupt Medien abspielt. Läuft keine Musik, wird kein blockierender Stop-Befehl an die Amazon-Cloud gesendet. Das spart sofort **1 bis 2 Sekunden Wartezeit** beim Öffnen des Mikrofons.
3. 🧠 **Kurzer, optimierter Standard-Prompt (ab v1.0.19):**  
   Der interne Prompt für Kurzantworten wurde auf maximale Prägnanz komprimiert. Dadurch generiert das KI-Modell deutlich weniger Füllwörter und antwortet in Bruchteilen einer Sekunde (schnellere *Time-To-First-Token*).
4. 🤖 **Wahl des schnellsten KI-Agenten:**  
   - Modelle wie **Google Gemini 2.0 Flash** oder schnelle OpenRouter-Modelle (wie **Llama 3.3 70B Instruct Free**) liefern Antworten in der Regel innerhalb von 1 bis 1,5 Sekunden.  
   - Für maximale Geschwindigkeit empfiehlt sich ein KI-Agent **ohne** Smart-Home-Entitätssteuerung (`assist`), damit kein unnötiger Geräte-Kontext geladen werden muss.

---

## 🛠️ Dienste (Services)

Die Integration stellt zwei native Home Assistant Dienste bereit:

| Dienst | Beschreibung | Parameter |
| :--- | :--- | :--- |
| `schlaue_antworten.start_dialog` | Startet den interaktiven Frage-Dialog auf einem Echo. | `echo_device` *(optional)* |
| `schlaue_antworten.ask_question` | Sendet eine Frage direkt an die KI und gibt das Ergebnis aus. | `question` *(erforderlich)*, `echo_device` *(optional)* |

---

## 📜 Versionshistorie & Changelog

| Version | Datum | Highlights |
| :--- | :--- | :--- |
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
