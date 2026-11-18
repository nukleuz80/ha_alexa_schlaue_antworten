#!/bin/sh
# Installs the Claude bridge for the current user (needs tmux and python3).
# Usage: install.sh <Home Assistant IP>   e.g. install.sh 192.168.1.10
set -e
HA_HOST="$1"
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/claude-alexa"
mkdir -p "$DEST/state" "$HOME/.config/claude-alexa" "$HOME/.config/systemd/user"
cp -f "$SRC/bridge.py" "$SRC/stop_hook.py" "$SRC/run_session.sh" "$SRC/settings.json" "$DEST/"
cp -f "$SRC/CLAUDE.md" "$DEST/"
chmod 755 "$DEST/run_session.sh" "$DEST/bridge.py" "$DEST/stop_hook.py"
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
cp -f "$SRC/claude-alexa-session.service" "$SRC/claude-alexa-bridge.service" "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now claude-alexa-session.service claude-alexa-bridge.service
systemctl --user restart claude-alexa-bridge.service
echo "Fertig. Token: $TOKEN_FILE"
