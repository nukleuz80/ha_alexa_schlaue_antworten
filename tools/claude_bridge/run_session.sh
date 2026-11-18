#!/bin/sh
# Runs inside tmux session "alexa" (started by claude-alexa-session.service).
# Keeps one Claude Code session alive, visible via Remote Control as "alexa".
# Working folder: CLAUDE_ALEXA_WORKDIR (default: the Home Assistant config).
# The session keeps a fixed id, so it never picks up another session there.
. "$HOME/.config/claude-alexa/env" 2>/dev/null
WORKDIR="${CLAUDE_ALEXA_WORKDIR:-/mnt/ha_config}"
STATE="$HOME/claude-alexa/state"
CLAUDE="$HOME/.local/bin/claude"
cd "$WORKDIR" || exit 1
mkdir -p "$STATE"
[ -s "$STATE/session_id" ] || cat /proc/sys/kernel/random/uuid > "$STATE/session_id"
ID="$(cat "$STATE/session_id")"
set -- --remote-control alexa --permission-mode auto \
  --settings "$HOME/claude-alexa/settings.json" \
  --append-system-prompt "$(cat "$HOME/claude-alexa/CLAUDE.md")"
while true; do
  # Resume the alexa conversation; the very first time it does not exist yet
  "$CLAUDE" --resume "$ID" "$@" || "$CLAUDE" --session-id "$ID" "$@"
  sleep 5
done
