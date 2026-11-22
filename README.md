<p align="center">
  <img src="www/schlaue_antworten/logo.png" alt="Schlaue Antworten Logo" width="180">
</p>

<h1 align="center">ALEXA - Schlaue Antworten</h1>
<p align="center"><b>KI-Sprachdialog für Amazon Alexa &amp; Home Assistant</b><br>
<i>Frag deinen Echo alles – Gemini, Claude, OpenAI oder ein lokales LLM antwortet. Und auf Wunsch arbeitet Claude Code für dich.</i></p>

<p align="center">
  <a href="https://github.com/nukleuz80/ha_alexa_schlaue_antworten/releases"><img src="https://img.shields.io/badge/version-1.5.9-blue.svg" alt="Version"></a>
  <a href="https://github.com/hacs/default"><img src="https://img.shields.io/badge/Marketplace%20(HACS)-Default-41BDF5.svg" alt="Marketplace Default"></a>
  <a href="https://www.home-assistant.io/"><img src="https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg" alt="Home Assistant"></a>
  <a href="#-mit-ki-entwickelt"><img src="https://img.shields.io/badge/entwickelt%20mit-KI--Unterst%C3%BCtzung-ff69b4?logo=sparkles&logoColor=white" alt="Mit KI-Unterstützung entwickelt"></a>
  <a href="https://github.com/nukleuz80/ha_alexa_schlaue_antworten/issues/new"><img src="https://img.shields.io/badge/Ideen%20%26%20W%C3%BCnsche-willkommen-brightgreen.svg" alt="Ideen willkommen"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
</p>

<p align="center">
  <a href="https://github.com/nukleuz80/ha_alexa_schlaue_antworten/wiki"><b>📖 Wiki</b></a> ·
  <a href="#-zwei-wege-zu-alexa">Zwei Wege</a> ·
  <a href="#-schnellstart">Schnellstart</a> ·
  <a href="#️-ablauf-im-alltag">Im Alltag</a> ·
  <a href="#-variante-3-sprachaufträge-an-claude-code-claude-brücke-eigener-skill">Claude-Brücke</a> ·
  <a href="#️-konfiguration-ui-options-flow">Konfiguration</a> ·
  <a href="#-ideen-wünsche--mitmachen">Ideen &amp; Wünsche</a> ·
  <a href="#-versionshistorie--changelog">Changelog</a>
</p>

---

**Schlaue Antworten** verbindet deine Amazon-Echo-Lautsprecher mit den KI-Agenten in Home Assistant (z. B. Google Gemini, Anthropic Claude, OpenAI, OpenRouter oder lokale LLMs). Komplett per Oberfläche eingerichtet – ohne YAML.

> [!NOTE]
> 📖 **Die ausführliche Dokumentation steht im [Wiki](https://github.com/nukleuz80/ha_alexa_schlaue_antworten/wiki):** [Installation](https://github.com/nukleuz80/ha_alexa_schlaue_antworten/wiki/Installation) · [Einrichtung & Optionen](https://github.com/nukleuz80/ha_alexa_schlaue_antworten/wiki/Einrichtung-und-Optionen) · [Sprachbefehle](https://github.com/nukleuz80/ha_alexa_schlaue_antworten/wiki/Sprachbefehle) · [Eigener Alexa-Skill](https://github.com/nukleuz80/ha_alexa_schlaue_antworten/wiki/Eigener-Alexa-Skill) · [Claude-Brücke](https://github.com/nukleuz80/ha_alexa_schlaue_antworten/wiki/Claude-Bruecke) · [Fehlerbehebung](https://github.com/nukleuz80/ha_alexa_schlaue_antworten/wiki/Fehlerbehebung)

> [!TIP]
> 🚀 **Welche KI-Modelle sind am schnellsten für Alexa?** → [**⚡ KI-Modelle & Speed-Guide**](docs/KI_MODELLE_SPEED_GUIDE.md) mit Latenz-Messungen, Free-Tier-Tipps und den schnellsten Anbietern.

---

## 🧭 Zwei Wege zu Alexa

| | 🎙️ **Eigener Skill** *(empfohlen)* | 🔔 **Community-Skill** *(ohne Entwicklerkonto)* |
| :--- | :--- | :--- |
| **Einrichtung** | ~10 Minuten: Skill in der kostenlosen Alexa-Entwicklerkonsole anlegen, Sprachmodell und Code per 📋-Knopf einfügen | ~3 Minuten: Community-Skill aktivieren, Alexa-Routine anlegen |
| **Geschwindigkeit** | ⚡ Antwort direkt als Skill-Antwort – kein Umweg über Routine, Schalter und Ansage | Umweg über Routine → Home Assistant → Ansage, spürbar langsamer |
| **Spracherkennung** | 🗣️ Ganze Sätze in einem Rutsch: *„Alexa, frag Schlaufuchs, wie weit ist der Mond?“* – auch mit Fragewörtern, Freitext und Folgefragen | Feste Auslöser über Routine, Frage im zweiten Schritt |
| **Richtiger Echo** | 🎯 Antwortet immer auf dem Echo, der gefragt wurde (eindeutige Geräte-ID) | Ermittelt den Echo über „zuletzt benutzt“ – kann danebenliegen |
| **Dialog** | 💬 Mikrofon bleibt offen, Vertiefung mit „Ja“, „aufs Handy“ | Vertiefung mit „Ja“, „aufs Handy“ |
| **Alexa-App** | 📱 Funktioniert auch in der Alexa-App (Sprache **und** Texteingabe) | – |
| **Claude Code** | 🤖 Sprachaufträge an Claude Code, Sitzungen per Sprache, Rückfragen per Push-Knopf | – |
| **Voraussetzung** | Öffentliche HTTPS-Adresse (z. B. Nabu Casa) | Alexa Media Player |

> [!TIP]
> **Community-Skill antwortet auf dem falschen Echo?** Frag Alexa vorher kurz *„Alexa, wie spät ist es?“* – danach gilt dieser Echo als „zuletzt benutzt“, und die nächste Antwort kommt zuverlässig dort an.

**Kurz:** Der Community-Skill ist der schnellste Einstieg. Wer Alexa täglich nutzt, wechselt zum **eigenen Skill** – er ist schneller, versteht mehr und kann deutlich mehr. Beide Wege lassen sich parallel betreiben (Sprachweg *„Beide“*).

<details>
<summary>🔒 <b>Datenschutz & Sicherheit (Klick zum Ausklappen)</b></summary>

- ✅ **Alles bleibt in deinem Home Assistant:** Fragen und Antworten laufen über deine eigenen KI-Agenten, kein fremder Server dazwischen.
- ✅ **Kein YAML:** keine Skripte, Helfer oder Template-Sensoren nötig.
- ✅ **Eigener Skill:** Er kennt nur eine geheime, zufällige Webhook-Adresse und ist an genau deinen Skill gekoppelt; fremde Skills werden abgewiesen. Der Code ist ein paar Zeilen Python ohne Abhängigkeiten.
- ✅ **Claude-Brücke:** nur im lokalen Netz, mit Token, nur für ausdrücklich erlaubte Echos, Rate-Limit und Ein/Aus-Schalter.
</details>

---

## ✨ Features

**🗣️ Sprechen & Antworten**
- ⚡ **Ein Satz genügt:** *„Alexa, frag Schlaufuchs, …“* (eigener Skill) bzw. *„Alexa, schlaue Frage: …“* (Community-Skill) – Antwort ohne Zwischenfrage.
- 💬 **Echter Dialog:** offenes Mikrofon, Folgefragen, auf Wunsch eine ausführlichere Vertiefung mit *„Ja“*.
- 🎯 **Antwort auf dem richtigen Echo** – per Geräte-ID (eigener Skill) oder „zuletzt benutzt“.
- 📱 **„Aufs Handy“:** schickt die Antwort als Push an die Companion-App.
- 🧹 **Für Sprache aufbereitet:** kurze Antworten, ohne Markdown-Sternchen und Sonderzeichen.

**🧠 KI & Zuverlässigkeit**
- 🤖 **Jeder KI-Agent aus Home Assistant:** Gemini, Claude, OpenAI, OpenRouter, lokale LLMs.
- 🛡️ **Ausweich-Agent im Wettlauf:** Antwortet der primäre Agent nicht schnell genug (Standard 2,5 s), startet der zweite parallel – die erste gute Antwort gewinnt.
- 🏠 **Smart-Home-Kontext:** Wetter, Uhrzeit, Raum und Anwesenheit fließen auf Wunsch in die Antwort ein.
- 📖 **Haus-Wiki:** eigene Notizen (Gäste-WLAN, Müllabfuhr, Notfallnummern), die die KI kennt.
- 🔄 **Schleifenschutz:** fragt bei Unverständlichem einmal nach und beendet dann leise.

**🤖 Claude Code per Sprache** *(eigener Skill)*
- 🗣️ **Aufträge an eine Claude-Code-Sitzung:** *„Alexa, frag Schlaufuchs, Claude soll nachsehen, welche Fenster offen sind.“* – die Antwort spricht derselbe Echo.
- 🗂️ **Sitzungen per Sprache:** neu starten, wechseln, auflisten, beenden.
- 🔘 **Rückfragen per Push-Knopf:** *Ja* / *Nein* / eigene Antwort direkt aus der Benachrichtigung.
- 📱 **Auch aus der Alexa-App** – per Sprache oder Texteingabe, Antwort als Push.

**⚙️ Einrichtung & Betrieb**
- 🚀 **Zero-YAML:** alles in der Oberfläche, inklusive 📋-Kopier-Knöpfen für Skill-Code und Sprachmodell.
- 📊 **Statistik-Sensor:** Anfragen heute, Dauer, Agent, Sprachweg und Mittelwerte.
- 📜 **Dialog-Verlauf** direkt in den Optionen.
- 🚨 **Ja/Nein-Fragen für Automationen:** `schlaue_antworten.interactive_question` feuert Events für deine Folge-Automationen.

---

## 📋 Schnellstart

### 1. Voraussetzungen
1. **Alexa Media Player** (Marketplace/HACS) – für Ansagen und die Echo-Erkennung.
2. **Ein KI-Agent in Home Assistant**, zum Beispiel:
   - 💡 **OpenRouter** *(Einstieg)*: kostenlose Modelle wie `meta-llama/llama-3.3-70b-instruct:free` – keine Kreditkarte nötig.
   - 🚀 **Google Generative AI (Gemini 2.5 Flash)**: sehr schnell, kostenloses Kontingent, exzellentes Deutsch.
   - 📖 Mehr dazu im [⚡ KI-Modelle & Speed-Guide](docs/KI_MODELLE_SPEED_GUIDE.md).

### 2. Integration installieren
1. **Marketplace** (ab HA 2026.11, vorher **HACS**) → nach **Schlaue Antworten** suchen → installieren → Home Assistant neu starten.
2. **Einstellungen ➔ Geräte & Dienste ➔ + Integration hinzufügen ➔ Schlaue Antworten**.
3. Primären KI-Agenten und Standard-Echo wählen.

### 3a. 🎙️ Eigener Skill *(empfohlen)*
1. In der [Alexa-Entwicklerkonsole](https://developer.amazon.com/alexa/console/ask) (kostenloses Konto) einen **Custom Skill** anlegen: Sprache *Deutsch*, **Alexa-hosted (Python)**, Region *EU (Irland)*.
2. In Schlaue Antworten: **Konfigurieren ➔ 🎙️ Eigener Alexa-Skill** → Link **„📋 … mit Kopier-Knöpfen öffnen“**.
3. **Sprachmodell kopieren** → *Build → JSON Editor* einfügen → *Save* → *Build*.
4. **Skill-Code kopieren** → *Code → lambda_function.py* ersetzen → *Deploy*.
5. *Test* auf **Development** stellen, unter *⚙️ Einstellungen* den Sprachweg auf **„Eigener Skill“** (oder „Beide“) setzen.
6. Fertig: *„Alexa, frag Schlaufuchs, wie weit ist der Mond?“* – einmal pro Echo *„Alexa, sag Schlaufuchs, du stehst in der Küche“* sorgt für die richtige Zuordnung.

### 3b. 🔔 Community-Skill *(ohne Entwicklerkonto)*
1. In der Alexa-App den kostenlosen Actionable-Notification-Skill aktivieren:  
   `amzn1.ask.skill.77bf0c24-791b-4993-9aaa-236298a83d40`
2. Alexa-Routine anlegen: **Wenn** *(Stimme)* `öffne schlaue antworten` → **Aktion** *Smart Home* → Schalter **„Schlaue Antworten: Dialog starten“** auf **AN**.
3. Fertig: *„Alexa, öffne Schlaue Antworten“* – oder ohne Routine direkt *„Alexa, schlaue Frage: …“*.

<details>
<summary>📦 <b>Für bestehende Setups / Legacy-YAML-Modus (Klick zum Ausklappen)</b></summary>

Falls du bereits ein bestehendes Setup aus früheren Versionen nutzt, bleibt alles zu **100 % abwärtskompatibel**:
- Die Integration prüft weiterhin automatisch, ob `sensor.last_alexa`, `input_boolean.alexa_ki_trigger` oder `script.activate_alexa_actionable_notification` existieren, und nutzt diese bevorzugt.
- Du musst bestehende Skripte, Helfer oder Szenen nicht löschen – sie funktionieren nahtlos weiter.
</details>

---

## ⚙️ Konfiguration (UI Options Flow)

Klicke in **Einstellungen ➔ Geräte & Dienste** bei **Schlaue Antworten** auf **Konfigurieren**. Das Menü hat fünf Punkte:

| Menüpunkt | Inhalt |
| :--- | :--- |
| ⚙️ **Einstellungen & Prompts** | KI-Agenten, Sprachweg, Texte, Prompts, Push-Ziel (Details unten) |
| 🎙️ **Eigener Alexa-Skill** | Aufrufname, Sprachmodell und Skill-Code mit 📋-Kopier-Knöpfen, Skill neu koppeln |
| 🔊 **Echo-Zuordnung** | Welche Alexa-Geräte-ID zu welchem Echo gehört (per Sprache: „du stehst in der Küche“) |
| 🤖 **Claude-Brücke** | Adresse, Token, erlaubte Echos, Alexa-App erlauben |
| 📜 **Verlauf** | Die letzten Dialoge mit Gerät, Frage, Antwort und Dauer |

Alle Optionen mit Standardwerten: [**Wiki → Einrichtung & Optionen**](https://github.com/nukleuz80/ha_alexa_schlaue_antworten/wiki/Einrichtung-und-Optionen)

<details>
<summary><b>⚙️ Einstellungen & Prompts im Detail (Klick zum Ausklappen)</b></summary>


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
- **Ziel-Gerät für Smartphone-Push:** Benachrichtigungsdienst für Antworten ans Handy, als Auswahlliste der vorhandenen Dienste. Fehlt das eingetragene Ziel, geht die Antwort an das einzige Handy mit Companion-App (seit v1.5.3). Empfohlen: `notify.mobile_app_<dein_handy>` – nur damit funktionieren die Antwort-Knöpfe bei Claude-Rückfragen.
- **Sprachbestätigung beim Senden aufs Smartphone:** Was Alexa sagen soll (Standard: *„Ich habe dir die Antwort aufs Handy geschickt.“*).
- **Bestätigungsansage bei Automatisierungs-Freigabe ('Ja'):** Text, wenn eine interaktive Automatisierungsfrage mit *„Ja“* beantwortet wird (Standard: *„Wird erledigt.“*).
- **Ausführlichere Vertiefung anbieten (Follow-up):** Fragt nach jeder Antwort, ob du mehr erfahren möchtest (Standard: *aktiviert*).
- **Fragetext für Vertiefung:** Eigener Text für die Nachfrage (Standard: *„Möchtest du eine ausführlichere Erklärung? Ja oder Nein?“*).
- **Abschiedstext bei Ablehnung ('Nein'):** Kurze Verabschiedung bei Ablehnung (Standard: *„Alles klar.“*).
- **Wiederholungsansage bei unverständlicher Frage:** Text für den ersten Fehlversuch (Standard: *„Das habe ich leider nicht verstanden. Bitte wiederhole deine Frage.“*).
- **Abbruchansage nach zweitem Fehlversuch:** Beendet den Dialog bei wiederholt unverständlicher Eingabe (Standard: *„Ich konnte dich leider wieder nicht verstehen. Versuche es bitte später noch einmal.“*).
- **KI-Prompts für Kurzantwort & Vertiefung:** Frei anpassbare System-Prompts mit Platzhaltern `{question}` und `{previous_answer}`.


</details>

---

## 🗣️ Ablauf im Alltag

### ⚡ Variante 1: Direktabfrage in einem Satz
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

### 🤖 Variante 3: Sprachaufträge an Claude Code (Claude-Brücke, eigener Skill)
1. **Du sagst:**  
   > *„Alexa, sag Schlaufuchs, Claude soll nachsehen, welche Fenster offen sind.“*  
   *(auch „… sag Claude …“, „… frag Claude …“, „… an Claude …“, „… Claude bitte …“)*
2. **Alexa bestätigt sofort:** *„Okay, ist bei Claude. Die Antwort kommt gleich hier.“*
3. **Der Auftrag landet in einer laufenden Claude-Code-Sitzung** (in tmux, per Remote Control auch in der Claude-App sichtbar).
4. **Wenn Claude fertig ist, spricht derselbe Echo den ersten Absatz der Antwort**; längere Antworten kommen zusätzlich aufs Handy.

**Sitzungen per Sprache (ab v1.1.0):**

| Du sagst („Alexa, sag Schlaufuchs, …“) | Was passiert |
| :--- | :--- |
| „… neue Claude-Sitzung Heizung prüf, warum das Bad kalt ist“ | Startet die Sitzung `heizung` (erstes Wort = Name) mit diesem ersten Auftrag; sie erscheint sofort in der Claude-App. Ohne Auftrag („… neue Claude-Sitzung Küche“) wartet sie. Folgeaufträge gehen dorthin. |
| „… wechsle zu Claude Heizung“ / „… wechsle zu Claude Hauptsitzung“ | „Claude soll …“ geht ab jetzt an diese Sitzung bzw. wieder an die Hauptsitzung `alexa`. |
| „… welche Claude-Sitzungen laufen?“ | Nennt alle Sitzungen und die aktive. |
| „… beende Claude Heizung“ | Beendet die Sitzung; Aufträge gehen wieder an die Hauptsitzung. |

**Aus der Alexa-App (ab v1.2.0):** Sag einmal in der Alexa-App auf dem Handy *„Alexa, sag Schlaufuchs, das ist mein Handy“* und schalte unter *🤖 Claude-Brücke* **Alexa-App erlauben** ein. Danach funktionieren alle Claude-Befehle auch aus der App, per Sprache oder Texteingabe; Claudes Antwort kommt vollständig als Push aufs Handy statt als Ansage.

**Lange Aufträge in zwei Schritten (ab v1.4.0):** Alexa hört bei der ersten kurzen Pause auf zuzuhören. Sag deshalb nur *„Alexa, frag Schlaufuchs, Claude soll“* – Alexa fragt *„Was soll ich Claude sagen?“*, und dein **ganzer nächster Satz** geht an Claude, ohne dass du „Claude“ noch einmal sagen musst (auch „ja“/„nein“ als Antwort auf eine Rückfrage).

**Rückfragen von Claude (ab v1.3.0):** Braucht Claude eine Entscheidung, kommt die Frage mit **Knöpfen in der Push-Nachricht** (z. B. *Ja* / *Nein*, bis zu drei Vorschläge) und – wenn Platz ist – einem Feld **Antworten** für eigenen Text. Ein Tipp schickt die Antwort in genau die Sitzung, die gefragt hat; Claudes nächste Antwort kommt wieder auf den Echo bzw. aufs Handy. Per Sprache geht es auch: *„Alexa, sag Schlaufuchs, antworte Claude ja.“* Voraussetzung: Push-Ziel ist die Companion-App (`notify.mobile_app_…` oder eine Gruppe daraus).

Höchstens 3 Sprach-Sitzungen neben der Hauptsitzung (`CLAUDE_ALEXA_MAX_SESSIONS`); nach 2 Stunden ohne Auftrag enden sie von selbst (`CLAUDE_ALEXA_IDLE_SECONDS`). Antworten einer Sprach-Sitzung beginnen mit ihrem Namen. Zum Zuschauen: `tmux -L alexa-x attach -t heizung`. Jede Sitzung verbraucht Claude-Kontingent.

**Einrichtung** (Schritt für Schritt im [Wiki → Claude-Brücke](https://github.com/nukleuz80/ha_alexa_schlaue_antworten/wiki/Claude-Bruecke)):
- Auf dem Rechner mit Claude Code (tmux und python3 nötig): `tools/claude_bridge/install.sh <IP von Home Assistant>` ausführen. Das legt `~/claude-alexa` an, erzeugt ein Token in `~/.config/claude-alexa/token` und startet zwei systemd-User-Dienste: `claude-alexa-session` (Sitzung „alexa“ in tmux mit Stop-Hook, Arbeitsordner `/mnt/ha_config` oder `CLAUDE_ALEXA_WORKDIR` aus `~/.config/claude-alexa/env`, feste Session-ID) und `claude-alexa-bridge` (HTTP auf Port 8765, nimmt nur Anfragen von Home Assistant an). Ist der Arbeitsordner für Claude Code noch neu, einmal `tmux -L alexa attach -t alexa` und ihn als vertrauenswürdig bestätigen.
- In Schlaue Antworten unter *🤖 Claude-Brücke*: Adresse (z. B. `http://192.168.1.50:8765`), Token und **erlaubte Echos** eintragen. Nur Echos, die unter *🔊 Echo-Zuordnung* zugeordnet **und** hier erlaubt sind, dürfen Aufträge schicken; der Standard-Echo zählt nicht.
- Neues Sprachmodell in die Alexa-Entwicklerkonsole einfügen und bauen (neuer `ClaudeIntent`).
- Der Schalter **„Claude-Brücke“** schaltet die Weitergabe jederzeit ab. Höchstens 6 Aufträge in 10 Minuten.

> ⚠️ Jeder in Hörweite eines erlaubten Echos kann der Claude-Sitzung Aufträge geben. Läuft sie im Auto-Modus, darf sie ohne Rückfrage handeln – erlaube nur Echos in Räumen, denen du vertraust.

---

## ⚡ Performance- & Latenz-Tipps

> 📖 **Ausführlicher Speed-Guide:** Eine vollständige Übersicht über die schnellsten LLMs der Welt (inkl. Latenz-Benchmarks und Hardware-Beschleunigern wie Cerebras & Groq) findest du im [**⚡ KI-Modelle & Speed-Guide**](docs/KI_MODELLE_SPEED_GUIDE.md).

1. 🔇 **Modellansage deaktivieren:** Spart ca. 1,5 Sekunden reine Sprechzeit pro Antwort.
2. 🏎️ **Smarte Musik-Vorprüfung:** Läuft keine Musik, wird kein blockierender Cloud-Stop-Befehl gesendet (spart 1–2 Sekunden beim Dialogstart).
3. 🤖 **Websuche in OpenRouter ausschalten:** In OpenRouter `web_search: off` stellen, um Suchmaschinen-Wartezeiten zu vermeiden (Antwort in 1–2 Sekunden).
4. ⚡ **Schnelle Modelle wählen:** Nutze vorzugsweise *Google Gemini 2.5 Flash* oder *Meta Llama 3.3 70B*.

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
| **v1.5.9** | 22.11.2026 | **Claude-Brücke, HA-Chat:** Der Stop-Hook schickt jetzt die ganze Runde an Home Assistant, also auch die Zwischenantworten, die Claude zwischen Werkzeugaufrufen schreibt. Bisher kam nur der letzte Textblock an. Alexa liest weiterhin nur die Schlussantwort vor. |
| **v1.5.8** | 22.11.2026 | **Claude-Brücke:** Sitzungsnamen unter `app` jetzt genau wie in der Claude-App: zuerst der mit `/rename` vergebene Name, sonst der Remote-Control-Name (bei Sitzungen der Brücke z. B. `alexa`, `ha-chat`), sonst der Ordnername. Der automatisch erzeugte KI-Titel wird nicht mehr verwendet. |
| **v1.5.7** | 22.11.2026 | **Claude-Brücke:** `GET /sessions` meldet zusätzlich unter `app` alle laufenden Claude-Code-Sitzungen dieses Rechners, die mit der Claude-App verbunden sind (Remote Control), mit dem Titel aus der App und dem Link dorthin. Damit zeigt *Agent Code Sessions* (ab v1.7.2) genau diese Sitzungen. |
| **v1.5.6** | 22.11.2026 | **Claude-Brücke:** Eine frisch gestartete Sitzung wird nicht mehr sofort wieder vergessen, wenn Home Assistant direkt nach dem Start die Sitzungsliste abfragt (90 s Schonfrist, bis die tmux-Sitzung läuft). Vorher landete die erste Chat-Nachricht dadurch in einem zweiten Startversuch und kam nie an. Neu installieren: `tools/claude_bridge/install.sh <HA-IP>`. |
| **v1.5.5** | 22.11.2026 | **Claude-Brücke für den Home-Assistant-Chat:** Die Brücke (`tools/claude_bridge`) nimmt jetzt auch Nachrichten aus dem Chat-Panel der Integration *Agent Code Sessions* an (`"source": "ha_chat"`). Sie bekommen das Präfix `[HA-Chat]`, dürfen bis 4000 Zeichen lang sein, wechseln nie die aktive Sprach-Sitzung und haben eigene Chat-Sitzungen (max. 3, ohne Leerlauf-Ende). Der Stop-Hook schickt die Antwort mit Prompt-ID und Antwort-Token an Home Assistant zurück; Alexa- und Chat-Antworten einer Sitzung kommen sich nicht mehr in die Quere. Auch lange, von Claude Code als „eingefügt“ markierte Eingaben werden erkannt. Neu installieren: `tools/claude_bridge/install.sh <HA-IP>`. An Alexa ändert sich nichts. |
| **v1.5.4** | 20.11.2026 | **Fix:** „Cloud soll nachsehen, welche Türen offen sind“ ging an die KI-Antwort statt an Claude. Alexa ordnet einen Claude-Auftrag manchmal dem Auffang-Befehl zu (vor allem, wenn sie „Claude“ als „cloud“ versteht); dann bekam Gemini den ganzen Satz samt „cloud soll“. Jetzt erkennt Schlaue Antworten solche Sätze auch dort und schickt den Auftrag an die Claude-Brücke, sofern sie eingerichtet ist. Das Sprachmodell muss dafür nicht neu kopiert werden. |
| **v1.5.3** | 19.11.2026 | **Fix:** Push ans Handy scheiterte, wenn das Ziel `notify.notify` war und es diesen Dienst nicht gibt (z. B. ohne Benachrichtigungsgruppe). Jetzt geht die Antwort in dem Fall an das einzige Handy mit Companion-App, und Alexa bestätigt nur noch, was wirklich gesendet wurde. In den *Einstellungen* ist das Ziel eine Auswahlliste der vorhandenen Dienste (Handys zuerst); ein vertippter Dienst wird vor dem Speichern gemeldet. Neue Installationen starten direkt mit dem Handy. |
| **v1.5.2** | 19.11.2026 | **Fix:** „Translation error: INVALID_TAG“ im Punkt *Eigener Alexa-Skill* – der Kopier-Link steckt jetzt im Platzhalter statt im Übersetzungstext; ein Test verhindert HTML-Tags in Übersetzungen. Doku überarbeitet (Vergleich der Sprachwege, Tipp „falscher Echo“). |
| **v1.5.1** | 19.11.2026 | Kopier-Link öffnet sich in einem neuen Tab (vorher sprang die App zur Startseite); die Einstellungen bleiben offen. Knopf „Fertig – Tab schließen“. |
| **v1.5.0** | 19.11.2026 | **Kopier-Knöpfe:** Im Punkt *🎙️ Eigener Alexa-Skill* öffnet ein Link (signiert, 30 Minuten gültig) eine Seite mit Sprachmodell und Skill-Code und je einem 📋-Knopf – kein Markieren mehr. **Fix zu v1.4.0:** Der Freitext-Slot heißt jetzt `freitext` (Alexa: „Slot cannot reference more than one slot type“). **Skill-Code und Sprachmodell beide neu einfügen.** |
| **v1.4.0** | 19.11.2026 | **Claude in zwei Schritten:** „Claude soll“ ohne Auftrag fragt „Was soll ich Claude sagen?“ und schickt den ganzen nächsten Satz an Claude – gegen abgeschnittene Aufträge und das schlecht erkannte Wort „Claude“. Neuer **Freitext-Intent** (eigener Slot-Typ `FREITEXT`) fängt Sätze ohne bekannten Anfang auf; im normalen Dialog gehen sie als Frage an die KI statt ins „nicht verstanden“. Neues Sprachmodell einfügen und bauen. |
| **v1.3.2** | 19.11.2026 | **Fix:** Speichern der *Einstellungen* löschte die Optionen der Claude-Brücke (URL, Token, Echos, Alexa-App) – jetzt bleiben alle anderen Optionen erhalten. Hinweis: Knöpfe für Claude-Rückfragen brauchen als Push-Ziel die Companion-App (`notify.mobile_app_…`), nicht `notify.notify`. |
| **v1.3.1** | 19.11.2026 | Rückfragen robuster: Auswahldialoge (AskUserQuestion) in den Alexa-Sitzungen gesperrt (`settings.json`), eine Frage mit 2–3 kurzen Listenpunkten wird ebenfalls zu Knöpfen. Brücke bestätigt Aufträge sofort und tippt im Hintergrund (kein Abbruch mehr direkt nach einem Sitzungs-Neustart). Brücke neu installieren. |
| **v1.3.0** | 19.11.2026 | **Rückfragen per Knopf:** Claude beendet Rückfragen mit `Optionen: Ja \| Nein`; daraus werden Knöpfe (max. 3) plus Freitext-Feld in der Push-Nachricht. Die Antwort geht per `mobile_app_notification_action` in die fragende Sitzung (Brücke: `/prompt` mit `session`). Neue Sprachbefehle „antworte Claude …“ / „Antwort an Claude …“. Brücke (`tools/claude_bridge`) neu installieren, Sprachmodell neu bauen. |

<details>
<summary>📚 <b>Ältere Versionen (51) anzeigen</b></summary>

| Version | Datum | Highlights |
| :--- | :--- | :--- |
| **v1.2.2** | 19.11.2026 | Claude-Antworten ohne 📊-Statistikzeile (wird aus Ansage und Push gefiltert, Sitzungsregel ergänzt). |
| **v1.2.1** | 19.11.2026 | **„Claude“ besser erkannt:** Alexa schreibt „Claude“ oft als „Cloud“, „Coth“, „Klod“ o. ä. – alle Claude-Befehle haben jetzt diese Schreibvarianten im Sprachmodell. Neues Sprachmodell einfügen und bauen. |
| **v1.2.0** | 18.11.2026 | **Claude-Aufträge aus der Alexa-App:** „Alexa, sag Schlaufuchs, das ist mein Handy“ (in der Alexa-App gesagt) merkt sich die App als Handy. Mit der neuen Option *Alexa-App erlauben* (Punkt *🤖 Claude-Brücke*, Standard aus) gehen Sprach- und Texteingaben aus der App an Claude; die Antwort kommt vollständig als Push aufs Handy. Neues Sprachmodell einfügen und bauen. |
| **v1.1.0** | 18.11.2026 | **Claude-Sitzungen per Sprache:** „Alexa, sag Schlaufuchs, neue Claude-Sitzung Heizung prüf das Bad“ startet eine eigene Claude-Code-Sitzung (in der Claude-App sichtbar) mit erstem Auftrag. Dazu „wechsle zu Claude …“, „welche Claude-Sitzungen laufen“ und „beende Claude …“. Höchstens 3 Sprach-Sitzungen, Ende nach 2 Stunden ohne Auftrag, jede Sitzung meldet ihre Antwort mit ihrem Namen an den Echo, der gefragt hat. Die Brücke schließt Hinweisfenster von Claude vor dem Tippen und prüft, ob ein Auftrag wirklich angekommen ist, sonst tippt sie ihn erneut. Neues Sprachmodell einfügen und bauen; auf dem Claude-Rechner `install.sh` erneut ausführen. |
| **v1.0.46** | 18.11.2026 | **Claude-Sitzung wird überwacht:** Die Sitzung „alexa“ läuft auf einem eigenen tmux-Socket (`tmux -L alexa attach -t alexa`), und systemd startet sie mit `Restart=always` neu, wenn tmux selbst wegfällt. Bisher startete nur die Schleife im Skript Claude neu, eine beendete tmux-Sitzung blieb weg. Nur `tools/claude_bridge` geändert; `install.sh` erneut ausführen. |
| **v1.0.45** | 18.11.2026 | **Claude-Brücke robuster:** Die Sitzung „alexa“ läuft jetzt im Home-Assistant-Ordner (einstellbar über `CLAUDE_ALEXA_WORKDIR`) mit fester Session-ID, damit sie nach einem Neustart genau ihr Gespräch fortsetzt und nie eine andere Sitzung im selben Ordner übernimmt. Die Sprachregeln kommen als Zusatz zum System-Prompt. Die Brücke drückt Enter erneut, wenn ein Auftrag direkt nach dem Start im Eingabefeld hängen bleibt. Nur `tools/claude_bridge` geändert; dort `install.sh` erneut ausführen. |
| **v1.0.44** | 18.11.2026 | **Claude-Brücke:** Mit „Alexa, sag Schlaufuchs, Claude soll …“ geht ein Sprachauftrag an eine laufende Claude-Code-Sitzung. Alexa bestätigt sofort; wenn Claude fertig ist, spricht derselbe Echo den ersten Absatz der Antwort, längere Antworten kommen zusätzlich aufs Handy. Neuer Optionspunkt *🤖 Claude-Brücke* (Adresse, Token, erlaubte Echos), neuer Schalter „Claude-Brücke“, Limit von 6 Aufträgen in 10 Minuten. Nur zugeordnete und erlaubte Echos dürfen Aufträge schicken. Die Gegenstelle für den Rechner mit Claude Code liegt in `tools/claude_bridge` (Brücke, Stop-Hook, tmux-Sitzung, systemd-Dienste, `install.sh`). Neues Sprachmodell einfügen und bauen, der Skill-Code bleibt. |
| **v1.0.43** | 13.11.2026 | **Echo-Zuordnung im eigenen Skill:** Sag am jeweiligen Echo einmal „Alexa, sag Schlaufuchs, du stehst in der Küche“ (auch „dieser Echo steht im Bad“, „ich bin im Wohnzimmer“) – Schlaue Antworten sucht den passenden Echo aus Alexa Media anhand von Name und Bereich und merkt sich die Zuordnung. Danach kennt die KI bei jeder Frage den richtigen Raum, und „Aufs Handy“ findet die letzte Antwort genau dieses Echos. Neuer Optionspunkt *🔊 Echo-Zuordnung* zeigt alle Echos, die den Skill benutzt haben, zum Zuordnen und Korrigieren. Ohne Zuordnung gilt weiter der Standard-Echo. Automatisches Lernen über „zuletzt angesprochen“ ist nicht möglich, weil Alexa Media Skill-Anfragen nicht meldet. Neues Sprachmodell einfügen und bauen, der Skill-Code bleibt. |
| **v1.0.42** | 13.11.2026 | **Aufs Handy im eigenen Skill:** „Schick es mir aufs Handy“ sendet die letzte Antwort als Push-Nachricht und bestätigt mit dem eingestellten Satz – im Gespräch die Antwort aus der Sitzung (liegt die ausführliche Antwort schon bereit, kommt diese), danach noch 15 Minuten lang die letzte Antwort dieses Echos („Alexa, sag Schlaufuchs, schick es aufs Handy“). „… und schick es mir aufs Handy“ direkt in der Frage beantwortet und sendet zugleich. Neue Beispielsätze im Sprachmodell (Sprachmodell neu einfügen und bauen, der Skill-Code bleibt). |
| **v1.0.41** | 13.11.2026 | **Ausführliche Antworten deutlich schneller:** Während Alexa „Ja oder Nein?“ fragt, rechnet die KI die ausführliche Antwort schon im Hintergrund; ein „Ja“ bekommt sie dann meist sofort, ein „Nein“ bricht die Berechnung ab. Für die Vertiefung starten beide KI-Agenten gleichzeitig, und der Standard-Prompt verlangt nur noch 2 bis 3 kurze Sätze (ein unveränderter alter Standard-Prompt wird automatisch ersetzt). Verspätet per Push zugestellte Vertiefungen zählen in der Statistik jetzt als ausführliche Antwort. |
| **v1.0.40** | 12.11.2026 | **Keine Endlosschleife bei unverständlichen Sätzen im eigenen Skill:** Versteht Alexa einen Satz nicht, fragt der Skill genau einmal nach; beim zweiten Mal endet das Gespräch mit der Abbruchansage. Das Sprachmodell versteht jetzt auch im offenen Gespräch „frag schlaufuchs …“ und „öffne schlaufuchs“ (neues Sprachmodell einfügen und bauen, der Skill-Code bleibt). Der Sensor zeigt die letzte Skill-Anfrage mit Intent, Text und Antwort zur Fehlersuche. |
| **v1.0.39** | 12.11.2026 | **Vertiefung per Ja/Nein im eigenen Skill:** Ist *Nachfrage für ausführlichere Erklärung* eingeschaltet, hängt der Skill an die Kurzantwort die Nachfrage an und merkt sich Frage und Kurzantwort in der Alexa-Sitzung. „Ja“ holt sofort die ausführliche Antwort (mit dem Vertiefungs-Prompt), „Nein“ verabschiedet sich – bei offenem Dialog fragt Alexa stattdessen „Noch eine Frage?“. Kein Warten und keine geplante Folgefrage mehr wie beim Community-Weg. Der Skill-Code bleibt unverändert. |
| **v1.0.38** | 12.11.2026 | **Dialogmodus im eigenen Skill:** Neue Option *Dialog offen halten* im Punkt *🎙️ Eigener Alexa-Skill*. Nach jeder Antwort fragt Alexa „Noch eine Frage?“ und hört weiter zu – so lassen sich mehrere Fragen hintereinander stellen, ohne jedes Mal „Alexa“ zu sagen. „Ja“ führt zur nächsten Frage, „Nein“ oder „Stopp“ beenden den Dialog mit dem Abschiedstext. Der Skill-Code bleibt unverändert. |
| **v1.0.37** | 12.11.2026 | **Skill-Code und Sprachmodell für den eigenen Skill:** Neuer Optionspunkt *🎙️ Eigener Alexa-Skill* zeigt den fertigen Skill-Code (mit deiner geheimen Adresse), das Sprachmodell für den JSON-Editor der Alexa-Entwicklerkonsole, den Status von Webhook und Kopplung sowie die letzte Frage über den Skill. Aufrufname einstellbar, Standard *schlaufuchs*. Das Sprachmodell hat einen eigenen Intent pro Fragewort (wer, was, wie, wo, wann, warum, welche … sowie ist, gibt es, erklär mir, übersetze), damit die ganze Frage ankommt. Der Skill-Code ist bewusst schlank und reicht alles an Home Assistant weiter, so dass spätere Verbesserungen ohne neues Einfügen ankommen. Start („Alexa, öffne Schlaufuchs“), Stopp, Hilfe und unverständliche Fragen werden beantwortet. |
| **v1.0.36** | 12.11.2026 | **Grundlage für den eigenen Alexa-Skill:** Neue Option *Sprachweg* (Community-Skill wie bisher, eigener Skill oder beide; Standard bleibt Community). Mit eigenem Skill nimmt Schlaue Antworten Fragen über eine geheime Webhook-Adresse entgegen und gibt die Antwort direkt in der Rückmeldung zurück, damit Alexa sie sofort spricht – ohne Umweg über Alexa Media. Der erste Skill, der die Adresse aufruft, wird gekoppelt, alle anderen werden abgewiesen; dazu Prüfung der Anfragen und eine Begrenzung auf 20 Fragen pro Minute. Der Skill-Weg wartet höchstens 6 Sekunden und liefert spätere Antworten aufs Handy nach. Neuer Knopf *Skill-Kopplung zurücksetzen* erzeugt eine neue Adresse. Skill-Code und Einrichtung folgen in der nächsten Version. |
| **v1.0.35** | 12.11.2026 | **Zeitbudget mit Nachlieferung aufs Handy:** Hat nach dem neuen Zeitbudget (Standard 6 s ab der Frage, einstellbar unter *Einstellungen & Prompts*) noch kein Agent geantwortet, sagt Alexa sofort *„Das dauert gerade zu lange, ich schicke dir die Antwort aufs Handy.“* (Text einstellbar). Die KI rechnet im Hintergrund weiter, die fertige Antwort kommt per Push an das eingestellte Benachrichtigungsziel und erscheint im Dialog-Log als *[Spät]*. 0 Sekunden schaltet das Zeitbudget ab. Beim Neuladen der Integration werden noch laufende Anfragen sauber abgebrochen. |
| **v1.0.34** | 12.11.2026 | **Wettlauf statt Warteschlange:** Antwortet der primäre Agent nicht innerhalb des neuen Zeitlimits (Standard 2,5 s, einstellbar unter *Einstellungen & Prompts*), startet der Ausweich-Agent parallel. Die erste gültige Antwort gewinnt, der langsamere Agent wird abgebrochen. Bei einem Fehler (z. B. 503) startet der Ausweich-Agent sofort, ohne das Zeitlimit abzuwarten. 0 Sekunden stellt das alte Verhalten ein (Ausweich-Agent nur bei Fehler). Das Dialog-Log zeigt die Zeiten beider Agenten. |
| **v1.0.33** | 12.11.2026 | **Neuer Antwort-Kern (Umbau ohne Verhaltensänderung):** Prompt-Bau, KI-Aufruf mit Fallback, Fehler- und Unklar-Erkennung, Bereinigung und Smart-Home-Kontext stecken jetzt im eigenen Modul `answer.py`. Die Sprachausgabe ist davon getrennt. Das ist die Grundlage für den kommenden eigenen Alexa-Skill und einen späteren Assist-Agenten. Neue Tests sichern das Verhalten ab. |
| **v1.0.32** | 12.11.2026 | **Antwortzeiten messen:** Jede Anfrage misst jetzt getrennt, wie lange die KI gebraucht hat (je Agent, auch beim Fallback) und wie lange alles zusammen gedauert hat. Das Dialog-Log zeigt Agent, KI-Zeit und Sprachweg (direkt, Dialog, Dienst). Der Sensor `sensor.alexa_schlaue_antworten_ki_anfragen_heute` hat neue Attribute: `letzte_ki_dauer_sekunden`, `letzter_agent`, `letzter_weg` sowie die Mittelwerte `mittlere_ki_dauer_sekunden` und `mittlere_gesamtdauer_sekunden` über die letzten 20 Anfragen. |
| **v1.0.31** | 29.10.2026 | **Vibe Coding Manifest & Badges:** Offizieller Hinweis und Badges zur leidenschaftlichen KI-gestützten Entwicklung (*„Vibe Coding mit voller Hingabe“*) in Dokumentation und Repository aufgenommen. |
| **v1.0.30** | 29.10.2026 | **Dokumentations-Offensive & Speed-Guide:** Neuer umfassender Praxis-Leitfaden [⚡ KI-Modelle & Speed-Guide](docs/KI_MODELLE_SPEED_GUIDE.md) mit detaillierten Latenz- und Throughput-Benchmarks (Tokens/s), Free-Tier-Empfehlungen (Google Gemini 2.5 Flash, OpenRouter Free Pool) und Hardware-Beschleuniger-Vergleich (Llama 3.3 70B via Cerebras/Groq). |
| **v1.0.29** | 27.10.2026 | **Wiederherstellung & Präzisions-Timing für Vertiefungs-Nachfragen:** 1) Zuverlässiges Auslösen der interaktiven Vertiefungs-Nachfrage (*„Möchtest du eine ausführlichere Erklärung? Ja oder Nein?“*) mit geöffnetem Mikrofon auch bei Antworten über 175 Zeichen; 2) Intelligentes TTS-Timing (~11 Zeichen/Sekunde + 1,8s Latenz-Puffer) mit Audio-Statusüberprüfung (`playing`-State-Guard) und 0,6s Cooldown verhindert jegliche Skill-Kollisionen und Simon-Says-Fehler; 3) Automatischer Abbruch bei gesprochenem Zwischenstopp (*„Alexa, Stopp“*); 4) Gerätebezogenes Task-Management (`_pending_followup_tasks`) mit sofortiger Stornierung bei neuen Dialogen oder Direktabfragen. |
| **v1.0.28** | 26.10.2026 | **Stabilitäts- & Timing-Update (Beseitigung von Simon Says & Ghost-Prompts):** 1) Task-Tracking & Abbruch veralteter Timer (`_cancel_pending_followup`); verhindert, dass alte Hintergrund-Timer nachfolgende Dialoge überschreiben; 2) Beseitigung des fehleranfälligen `asyncio.sleep`-Splits bei langen Antworten: Antworten über 170 Zeichen werden direkt vollständig via TTS abgespielt, wodurch die Fehlermeldung *„Bei dem Simon Says EU Skill ist ein Problem aufgetreten“* und verzögerte Geister-Nachfragen dauerhaft eliminiert werden; 3) Ein-Satz-Direktabfragen spielen Antworten unmittelbar ab (ohne interaktive Nachfrage); 4) Puffer-Schutz (`clean_text[:172]`) gegen 255-Zeichen-Overflows in `input_text.alexa_actionable_notification`. |
| **v1.0.27** | 25.10.2026 | **JSON-Sanitization für Alexa Actionable Notifications (Simon Says Fix):** Automatische Bereinigung von Anführungszeichen (`"`), kaufmännischen Und-Zeichen (`&`) und Backslashes vor Übergabe an den Actionable Notification Skill; verhindert JSON-Syntaxfehler im `input_text` und schützt vor der Amazon-Fehlermeldung *„Bei dem Simon Says EU Skill ist ein Problem aufgetreten“*. |
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

</details>

---

## 💡 Ideen, Wünsche & Mitmachen

**Feature-Wünsche, Ideen, Fehlerberichte und Verbesserungsvorschläge sind ausdrücklich erwünscht!** Viele Funktionen dieser Integration sind aus genau solchen Wünschen entstanden – jede Idee wird gelesen.

- 💡 **Idee oder Wunsch?** → [Issue eröffnen](https://github.com/nukleuz80/ha_alexa_schlaue_antworten/issues/new) und kurz beschreiben, was du dir wünschst. Kein Formular-Zwang, ein Satz reicht.
- 🐞 **Etwas klappt nicht?** → [Issue eröffnen](https://github.com/nukleuz80/ha_alexa_schlaue_antworten/issues/new) – hilfreich sind Version, Sprachweg (eigener Skill / Community) und der Text aus dem *📜 Verlauf*.
- ⭐ **Gefällt dir das Projekt?** Ein Stern auf GitHub hilft anderen, es zu finden.
- 🔧 **Pull Requests** sind willkommen – die Testsuite (`pytest`) sollte grün bleiben.

---

## 🤖 Mit KI entwickelt

Dieses Projekt entsteht **offen und mit Stolz mit KI-Unterstützung** („Vibe Coding“): Ideen, Anforderungen und Praxistests kommen aus dem echten Alltag eines Smart Homes, der Code entsteht im Dialog mit KI-Assistenten (u. a. Claude Code, Google Gemini/Antigravity).

- 🧑‍💻 **Mensch entscheidet:** Jede Funktion wird im eigenen Zuhause an echten Echos ausprobiert, bevor sie veröffentlicht wird.
- ✅ **Abgesichert durch Tests:** Über 80 automatische Tests laufen vor jeder Version.
- 🔍 **Transparent:** Der komplette Code und jede Änderung sind öffentlich nachvollziehbar.

---

## 📄 Lizenz
MIT License. Siehe [`LICENSE`](LICENSE) für Details.
