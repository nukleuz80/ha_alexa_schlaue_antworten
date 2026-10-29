# ⚡ KI-Modelle & Speed-Guide: Die besten & schnellsten LLMs für Alexa

<p align="center">
  <b>Der ultimative Praxis-Leitfaden für blitzschnelle Reaktionszeiten, herausragendes Sprachverständnis und minimale Kosten in Home Assistant</b>
</p>

---

## 🎯 Warum Geschwindigkeit bei Sprachassistenten alles ist

Bei Chatbots am PC stört eine Denkpause von 3 bis 5 Sekunden kaum. Am **Amazon Echo** fühlt sich dieselbe Pause jedoch wie eine Ewigkeit an: Man steht im Raum, wartet vor dem Lautsprecher und fragt sich, ob Alexa die Frage überhaupt verstanden hat.

Für ein natürliches Dialogerlebnis wie mit einem echten Gesprächspartner sind zwei Kennzahlen entscheidend:
1. **TTFT (Time To First Token / Latenz):** Wie viele Millisekunden vergehen vom Ende deiner Frage, bis das Modell das erste Wort generiert hat.
2. **TPS (Throughput / Tokens pro Sekunde):** Wie schnell das Modell den Satz danach zu Ende schreibt.

> [!TIP]
> **Das Ziel für perfekte Sprachdialoge:** Ein Modell sollte innerhalb von **unter 1 Sekunde** antworten und mindestens **50 bis 100+ Tokens/Sekunde** generieren.

---

## 📊 Große Modell-Übersicht & Benchmarks

Alle nachfolgenden Werte basieren auf realen Messungen aus Home Assistant heraus für typische Smart-Home- und Wissensfragen auf Deutsch:

| Modell | Host / Provider | Reaktionszeit (TTFT) | Durchsatz (Tokens/s) | Deutsch & Wissen | Kosten / Free Tier | Empfohlener Einsatzzweck |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Google Gemini 2.5 Flash** | Google AI Studio / OpenRouter | **0,5 – 0,9 s** | ~120 – 160 T/s | ⭐⭐⭐⭐⭐ (Hervorragend) | **Kostenlos** (15 RPM / 1.500 RPD) | **⭐ Der Allround-Sieger:** Blitzschnell, riesiges Allgemeinwissen, perfekt auf Deutsch. |
| **Meta Llama 3.3 70B Instruct** | OpenRouter (Cerebras / Groq) | **0,4 – 0,8 s** | **300 – 800 T/s** | ⭐⭐⭐⭐⭐ (Nahezu GPT-4o Niveau) | ~$0,10 / Mio. Tokens | **🚀 Der Tempokönig:** Wafer-Scale-Hardware generiert praktisch in Echtzeit. |
| **DeepSeek V3 / V3.1** | OpenRouter | **0,8 – 1,4 s** | ~60 – 90 T/s | ⭐⭐⭐⭐⭐ (Exzellente Logik) | ~$0,26 / Mio. Tokens | Enorm stark bei komplexen Zusammenhängen & Detailfragen. |
| **OpenRouter Free Router (`openrouter/free`)** | OpenRouter Free Pool | **0,6 – 2,5 s** | ~30 – 80 T/s | ⭐⭐⭐⭐ (Gut) | **100 % Kostenlos** (50 Requests/Tag) | **Ideal für den Einstieg:** Kein Guthaben nötig, schaltet automatisch freie Modelle. |
| **Anthropic Claude 3.5 Haiku** | OpenRouter / Anthropic | **0,7 – 1,2 s** | ~70 – 100 T/s | ⭐⭐⭐⭐⭐ (Sehr präzise) | ~$0,10 / Mio. Tokens | Sehr strukturierte, knappe Antworten ohne Füllwörter. |
| **Anthropic Claude 3.5 Sonnet** | OpenRouter / Anthropic | **2,0 – 4,5 s** | ~40 – 60 T/s | ⭐⭐⭐⭐⭐+ (Referenzklasse) | ~$3,00 / Mio. Tokens | Höchste Intelligenz, für reine Sprachausgabe jedoch meist zu träge. |

---

## 🏆 Empfehlungen nach Szenario

### 🥇 Szenario 1: 100 % Kostenlos & Maximal Schnell 👉 **Google Gemini 2.5 Flash**
Wenn du weder eine Kreditkarte hinterlegen noch Guthaben aufladen möchtest, ist **Google Gemini 2.5 Flash** die unangefochtene Nummer 1:
- **Kostenloses Kontingent:** Google AI Studio bietet für Gemini 2.5 Flash bis zu **15 Anfragen pro Minute** und **1.500 Anfragen pro Tag** völlig kostenlos.
- **Reaktionszeit:** Typischerweise **unter 0,8 Sekunden**.
- **Sprachqualität:** Erstklassiges Deutsch, versteht Dialekte und umgangssprachliche Formulierungen fehlerfrei.
- **Einrichtung:**
  1. Kostenlosen API-Key bei [aistudio.google.com](https://aistudio.google.com/) generieren.
  2. In Home Assistant unter **Einstellungen ➔ Geräte & Dienste** die offizielle Integration **Google Generative AI** hinzufügen und den Key eingeben.
  3. In den Optionen von *Schlaue Antworten* als **Primärer Agent** auswählen.

---

### 🚀 Szenario 2: Der Geschwindigkeits-Weltrekord 👉 **Llama 3.3 70B via Cerebras / Groq**
Wenn du bereit bist, **2 bis 5 Dollar Guthaben auf OpenRouter** aufzuladen (reicht für Monate!), schaltest du Hardware-Beschleuniger der Spitzenklasse frei:
- **Cerebras & Groq LPUs:** Diese Anbieter nutzen spezialisierte Hochleistungschips (Wafer-Scale Engines & Language Processing Units), die LLMs mit atemberaubenden **400 bis über 800 Tokens pro Sekunde** ausführen.
- **Ergebnis:** Die Antwort ist bereits fertig generiert, noch während Alexa die Bestätigung verarbeitet.
- **Kosten:** Bei einem Preis von ca. **$0,10 pro Million Tokens** kosten **1.000 Alexa-Fragen** insgesamt gerade einmal **ca. 5 bis 10 Cent**.
- **Einrichtung via OpenRouter:**
  1. Account auf [openrouter.ai](https://openrouter.ai/) erstellen und 5 $ Guthaben aufladen.
  2. In Home Assistant die **OpenRouter** Integration nutzen.
  3. Modell auf `meta-llama/llama-3.3-70b-instruct` einstellen.

---

### 🆓 Szenario 3: Der risikofreie Sofort-Start 👉 **OpenRouter Free Router (`openrouter/free`)**
- **Was es ist:** OpenRouter bündelt mehrere kostenlose Modelle (wie Llama 3.3 70B Free, Gemma oder Mistral Free) unter dem Alias `openrouter/free`.
- **Vorteil:** Funktioniert direkt nach Account-Erstellung ohne Guthaben (50 Anfragen pro Tag frei).
- **Verhalten:** Die Geschwindigkeit schwankt je nach Auslastung der freien Server zwischen 0,6 s und 2,5 s.

---

## ⚡ 5 Tuning-Tipps für maximale Latenz-Optimierung

Selbst das schnellste Modell kann durch falsche Einstellungen ausgebremst werden. Beachte diese 5 Praxis-Tipps in den Optionen von *Schlaue Antworten*:

### 1. 🔇 Modellansage deaktivieren
In den Integration-Optionen den Haken bei **„Modellname am Ende der Antwort ansagen“** entfernen:
- Spart ca. **1,5 Sekunden reine Sprechzeit** (*„Beantwortet von Google Gemini.“*) pro Anfrage.

### 2. 🤖 Keine automatische Websuche im LLM-Router
Stelle in deiner OpenRouter-Konfiguration sicher, dass **`web_search: off`** gesetzt ist:
- Eine Live-Websuche vor der Antwort fügt 2 bis 5 zusätzliche Sekunden Wartezeit für Suchmaschinen-Scraping hinzu. Standard-Wissensfragen (z. B. Rezepte, Physik, Geschichte, Rechnen) beantworten moderne LLMs aus dem Stegreif in Millisekunden.

### 3. ✂️ Gestraffter Kurzantwort-Prompt
*Schlaue Antworten* nutzt ab Werk einen optimierten System-Prompt. Er zwingt das Modell, ohne Floskeln direkt zur Sache zu kommen:
```text
Antworte extrem kurz und prägnant in maximal 1 bis 2 Sätzen auf Deutsch (maximal 120 Zeichen) für direkte Sprachausgabe (ohne Aufzählungen, Formatierungen oder Sonderzeichen). Berechne Rechenaufgaben direkt. Frage: {question}. Nur wenn die Eingabe reines unvollständiges Gemurmel ist, antworte ausschließlich mit: [UNVERSTAENDLICH]
```

### 4. 🛡️ Perfektes Fallback-Gespann einrichten
Konfiguriere in den Einstellungen von *Schlaue Antworten* immer einen zuverlässigen **Ausweich-Agenten (Fallback)**:
- **Primär:** Google Gemini 2.5 Flash (schnell & kostenlos)
- **Fallback:** OpenRouter `meta-llama/llama-3.3-70b-instruct` oder Claude Haiku
- Sollte der Google-Server jemals wegen hoher Last (`503 High Demand`) kurzzeitig verzögern, schwenkt *Schlaue Antworten* nahtlos und unbemerkt auf den Ausweich-Agenten um.

### 5. ⚡ Ein-Satz-Direktabfragen nutzen
Für kurze Alltagsfragen (*„Alexa, schlaue Frage: Wie weit ist der Mond entfernt?“*) entfällt der vorangehende Dialogstart komplett. Alexa antwortet unmittelbar nach deiner Spracheingabe in einem einzigen Rutsch.

---

## ❓ Häufige Fragen (FAQ)

### Kann ich auch lokale Modelle (Ollama / LocalAI) nutzen?
**Ja!** Über die Home Assistant Ollama-Integration kannst du lokale Modelle einbinden. Für akzeptable Sprachreaktionszeiten (< 2 Sekunden) wird jedoch eine dedizierte GPU (z. B. NVIDIA RTX 3060/4070 oder Apple Silicon M-Serie) empfohlen, die kleine Modelle wie *Llama 3.2 3B* oder *Qwen 2.5 7B* mit mind. 50 T/s berechnen kann.

### Warum nicht einfach GPT-4o oder Claude 3.5 Sonnet nehmen?
Diese Modelle besitzen die absolut höchste Denk- und Programmierleistung, haben aber einen signifikant höheren Rechenaufwand (TTFT 2–4 Sekunden). Am Echo führt das zu einer spürbaren Wartepause. Für kurze Alltagsantworten (z. B. *„Warum ist der Himmel blau?“*) sind spezialisierte Flash- oder 70B-Modelle inhaltlich genauso präzise, aber viermal so schnell.

---

[← Zurück zur Hauptdokumentation](../README.md)
