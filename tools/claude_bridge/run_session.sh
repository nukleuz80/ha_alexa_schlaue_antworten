#!/bin/sh
# Runs inside tmux session "alexa" (started by claude-alexa-session.service).
# Keeps one Claude Code session alive, visible via Remote Control as "alexa".
cd "$HOME/claude-alexa" || exit 1
CLAUDE="$HOME/.local/bin/claude"
set -- --remote-control alexa --permission-mode auto \
  --add-dir /mnt/ha_config --settings "$HOME/claude-alexa/settings.json"
while true; do
  # Pick up the previous conversation; the first time there is none
  "$CLAUDE" --continue "$@" || "$CLAUDE" "$@"
  sleep 5
done
