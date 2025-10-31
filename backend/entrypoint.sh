#!/usr/bin/env bash
set -euo pipefail

USER_HOME="/home/app"
SRC_DIR="/host_gemini"
DEST_GEMINI_DIR="$USER_HOME/.gemini"
DEST_CFG_DIR="$USER_HOME/.config"

mkdir -p "$DEST_GEMINI_DIR" "$DEST_CFG_DIR/gemini" "$DEST_CFG_DIR/@google/gemini"

if [ -d "$SRC_DIR" ]; then
  # Copy everything from mounted host creds
  cp -a "$SRC_DIR"/. "$DEST_GEMINI_DIR"/ || true

  # If there is a config or config.json, mirror it into common locations
  if [ -f "$DEST_GEMINI_DIR/config.json" ]; then
    cp -f "$DEST_GEMINI_DIR/config.json" "$DEST_CFG_DIR/gemini/config.json" || true
    cp -f "$DEST_GEMINI_DIR/config.json" "$DEST_CFG_DIR/@google/gemini/config.json" || true
  fi
  if [ -f "$DEST_GEMINI_DIR/config" ]; then
    cp -f "$DEST_GEMINI_DIR/config" "$DEST_CFG_DIR/gemini/config" || true
    cp -f "$DEST_GEMINI_DIR/config" "$DEST_CFG_DIR/@google/gemini/config" || true
  fi
fi

# Fix ownership for non-root user
chown -R app:app "$USER_HOME/.gemini" "$DEST_CFG_DIR" || true

# Create data directory with proper permissions (for Docker volume)
mkdir -p /app/data || true
chown -R app:app /app/data || true

# Add user local bin to PATH for uvicorn and other Python tools
export PATH="$USER_HOME/.local/bin:$PATH"

exec "$@"




