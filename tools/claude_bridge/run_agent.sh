#!/bin/sh
# Runs one fixed agent inside tmux (socket "agent-<name>"), started by
# claude-agent@<name>.service. Keeps the Claude session alive, visible via
# Remote Control as <name>, and resumes the same conversation after restarts.
# Usage: run_agent.sh <name>   (model and settings come from agents.json)
NAME="$1"
. "$HOME/.config/claude-alexa/env" 2>/dev/null
BASE="$HOME/claude-alexa"
WORKDIR="${CLAUDE_ALEXA_WORKDIR:-/mnt/ha_config}"
STATE="$BASE/state/agents"
CLAUDE="$HOME/.local/bin/claude"
ROLE="$BASE/agents/$NAME.md"
[ -f "$ROLE" ] || { echo "Rolle fehlt: $ROLE" >&2; exit 1; }
cd "$WORKDIR" || exit 1
mkdir -p "$STATE"
[ -s "$STATE/$NAME.id" ] || cat /proc/sys/kernel/random/uuid > "$STATE/$NAME.id"
ID="$(cat "$STATE/$NAME.id")"
field() {
  python3 -c 'import json,sys
for a in json.load(open(sys.argv[1]))["agents"]:
    if a.get("name") == sys.argv[2]:
        print(a.get(sys.argv[3]) or "")' "$BASE/agents.json" "$NAME" "$1" 2>/dev/null
}
MODEL="$(field model)"
SETTINGS="$(field settings)"
SETTINGS="$BASE/${SETTINGS:-settings.json}"
set -- --remote-control "$NAME" --permission-mode auto --settings "$SETTINGS" \
  --append-system-prompt "$(cat "$BASE/agents/_common.md" "$ROLE")"
[ -n "$MODEL" ] && set -- --model "$MODEL" "$@"
while true; do
  "$CLAUDE" --resume "$ID" "$@" || "$CLAUDE" --session-id "$ID" "$@"
  sleep 5
done
