<p align="center">
  <img src="www/schlaue_antworten/logo.png" alt="Schlaue Antworten Logo" width="180">
</p>

<h1 align="center">Schlaue Antworten</h1>
<p align="center"><b>KI-Sprachdialog für Amazon Alexa &amp; Home Assistant</b></p>

<p align="center">
  <a href="https://github.com/nukleuz80/ha_alexa_schlaue_antworten/releases"><img src="https://img.shields.io/badge/version-1.0.3-blue.svg" alt="Version"></a>
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
- **Google Generative AI (Gemini):** z. B. eine reine Text-Instanz ohne Smart-Home-Entitätssteuerung für maximale Geschwindigkeit (~1,2s Antwortzeit).
- **Anthropic Claude / OpenRouter:** z. B. `conversation.anthropic_claude_sonnet_4`.
- **OpenAI / Local LLM / Ollama:** Beliebige `conversation.*`-Entität.

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
4. **Alexa liest dir die Antwort vor:**  
   Prägnant in 1–2 Sätzen, bereinigt um Markdown-Formatierungen und optional mit Nennung des Modells.

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
| **v1.0.3** | 23.10.2026 | Umfassende Dokumentationsüberarbeitung: Klarstellung der privaten Architektur (kein AWS Lambda / kein Entwicklerkonto nötig), Schritt-für-Schritt-Anleitung und Alltags-Beispiele. |
| **v1.0.2** | 23.10.2026 | Bild-Assets in dedizierten Ordner `www/schlaue_antworten/` verschoben und Pfade/Skripte bereinigt. |
| **v1.0.1** | 23.10.2026 | Offizielles Logo hinzugefügt (SVG- und PNG-Assets) und Dokumentations-Update. |
| **v1.0.0** | 23.10.2026 | Erstveröffentlichung als native Custom Integration mit vollständigem Options Flow, dynamischer Raum-Erkennung via `sensor.last_alexa`, 503-Ausweich-Logik (Fallback) und nahtloser Alexa Actionable Notifications Anbindung. |

---

## 📄 Lizenz
MIT License. Siehe [`LICENSE`](LICENSE) für Details.
