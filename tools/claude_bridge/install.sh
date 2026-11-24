#!/bin/sh
# Installs the Claude bridge for the current user (needs tmux and python3).
# Usage: install.sh <Home Assistant IP>   e.g. install.sh 192.168.1.10
set -e
HA_HOST="$1"
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/claude-alexa"
mkdir -p "$DEST/state" "$HOME/.config/claude-alexa" "$HOME/.config/systemd/user"
cp -f "$SRC/bridge.py" "$SRC/stop_hook.py" "$SRC/permission_hook.py" "$SRC/run_session.sh" "$SRC/run_voice_session.sh" "$SRC/settings.json" "$DEST/"
cp -f "$SRC/CLAUDE.md" "$SRC/run_agent.sh" "$SRC/settings_readonly.json" "$DEST/"
mkdir -p "$DEST/agents"
cp -f "$SRC"/agents/*.md "$DEST/agents/"
# agents.json is Jan's list of fixed agents: only copied the first time
[ -f "$DEST/agents.json" ] || cp "$SRC/agents.json" "$DEST/"
chmod 755 "$DEST/run_session.sh" "$DEST/run_voice_session.sh" "$DEST/run_agent.sh" "$DEST/bridge.py" "$DEST/stop_hook.py" "$DEST/permission_hook.py"
chmod 700 "$DEST/state"
TOKEN_FILE="$HOME/.config/claude-alexa/token"
if [ ! -s "$TOKEN_FILE" ]; then
  python3 -c "import secrets; print(secrets.token_urlsafe(32))" > "$TOKEN_FILE"
  chmod 600 "$TOKEN_FILE"
fi
ENV_FILE="$HOME/.config/claude-alexa/env"
if [ -n "$HA_HOST" ]; then
  echo "CLAUDE_ALEXA_ALLOWED=$HA_HOST,127.0.0.1" > "$ENV_FILE"
elif [ ! -f "$ENV_FILE" ]; then
  echo "Bitte die IP von Home Assistant angeben: $0 <IP>" >&2
  exit 1
fi
cp -f "$SRC/claude-alexa-session.service" "$SRC/claude-alexa-bridge.service" "$SRC/claude-agent@.service" "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now claude-alexa-session.service claude-alexa-bridge.service
for NAME in $(python3 -c 'import json,sys; print(" ".join(a["name"] for a in json.load(open(sys.argv[1]))["agents"]))' "$DEST/agents.json"); do
  systemctl --user enable --now "claude-agent@$NAME.service"
done
systemctl --user restart claude-alexa-bridge.service
echo "Fertig. Token: $TOKEN_FILE"
