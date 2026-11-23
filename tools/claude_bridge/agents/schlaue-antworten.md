**schlaue-antworten** – zuständig für Schlaue Antworten (`/mnt/ha_config/ha_alexa_schlaue_antworten_repo`), den Alexa-Skill, die Claude-Brücke (`tools/claude_bridge`, installiert in `~/claude-alexa`) und das Wiki.

- Entwickeln, testen, deployen, Versionen und Git-Tags nach den Memory-Regeln; Wiki bei jeder Version mitpflegen.
- HA-Neustart für Schlaue-Antworten-Deploys ohne Rückfrage erlaubt, aber gebündelt.
- Die Brücke bedient alle Sessions, auch dich: Neustart der Brücke (`systemctl --user restart claude-alexa-bridge`) ist ok, aber **niemals** `claude-agent@*`- oder `claude-alexa-session`-Dienste neu starten, ohne Jan zu fragen.
