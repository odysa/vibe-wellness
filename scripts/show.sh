#!/bin/bash
# Show the exercise overlay (with interval and single-instance guard)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/.."
LOCK_DIR="/tmp/vibe-wellness.lock"
INTERVAL_FILE="/tmp/vibe-wellness-interval"

# Atomic lock — mkdir is atomic across all processes/sessions
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    # Lock exists — check if overlay process is still alive
    if [ -f "$LOCK_DIR/pid" ]; then
        pid=$(cat "$LOCK_DIR/pid")
        if kill -0 "$pid" 2>/dev/null; then
            exit 0
        fi
    fi
    # Stale lock, clean up and retry
    rm -rf "$LOCK_DIR"
    mkdir "$LOCK_DIR" 2>/dev/null || exit 0
fi

# Read interval from config, fallback to 900 (15min)
INTERVAL_SECONDS=$(python3 -c "import json; print(json.load(open('$PROJECT_DIR/vibe_wellness/config.json')).get('interval', 900))" 2>/dev/null || echo 900)

# Skip if within interval
if [ -f "$INTERVAL_FILE" ]; then
    last=$(cat "$INTERVAL_FILE")
    now=$(date +%s)
    if (( now - last < INTERVAL_SECONDS )); then
        rm -rf "$LOCK_DIR"
        exit 0
    fi
fi

# Launch overlay; clean up lock when it exits
(
    uv run --project "$PROJECT_DIR" python -m vibe_wellness
    rm -rf "$LOCK_DIR"
) &
echo $! > "$LOCK_DIR/pid"
date +%s > "$INTERVAL_FILE"
