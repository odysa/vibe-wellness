#!/bin/bash
# Hide the exercise overlay

LOCK_DIR="/tmp/vibe-wellness.lock"

if [ -f "$LOCK_DIR/pid" ]; then
    pid=$(cat "$LOCK_DIR/pid")
    kill "$pid" 2>/dev/null
fi
rm -rf "$LOCK_DIR"
