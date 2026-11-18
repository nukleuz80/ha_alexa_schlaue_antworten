#!/bin/sh
# Runs one voice session inside tmux (socket "alexa-x"), started by bridge.py.
# Usage: run_voice_session.sh <name> <claude session id>
# It is not restarted: when Claude exits, the voice session is over.
. "$HOME/.config/claude-alexa/env" 2>/dev/null
WORKDIR="${CLAUDE_ALEXA_WORKDIR:-/mnt/ha_config}"
cd "$WORKDIR" || exit 1
exec "$HOME/.local/bin/claude" --session-id "$2" --remote-control "$1" \
  --permission-mode auto --settings "$HOME/claude-alexa/settings.json" \
  --append-system-prompt "$(cat "$HOME/claude-alexa/CLAUDE.md")"
