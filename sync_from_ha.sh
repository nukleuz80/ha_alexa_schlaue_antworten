#!/bin/bash
set -e
REPO_DIR="/config/ha_alexa_schlaue_antworten_repo"

echo "Syncing Schlaue Antworten files from Home Assistant..."
rsync -av --delete --exclude="__pycache__" /config/custom_components/schlaue_antworten/ "$REPO_DIR/custom_components/schlaue_antworten/"

echo "Schlaue Antworten repository synchronized successfully."
