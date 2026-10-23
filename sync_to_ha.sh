#!/bin/bash
set -e
REPO_DIR="/config/ha_alexa_schlaue_antworten_repo"

echo "Deploying Schlaue Antworten files to Home Assistant..."
mkdir -p /config/custom_components/schlaue_antworten /config/www/schlaue_antworten
rsync -av --delete --exclude="__pycache__" "$REPO_DIR/custom_components/schlaue_antworten/" /config/custom_components/schlaue_antworten/
cp -rf "$REPO_DIR/www/schlaue_antworten/"* /config/www/schlaue_antworten/ 2>/dev/null || true

echo "Schlaue Antworten deployed to Home Assistant successfully."
