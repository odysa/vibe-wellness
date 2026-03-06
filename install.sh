#!/bin/bash
# Install vibe-wellness: config dir, Claude Code hook, dependencies
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="$HOME/.config/vibe-wellness"
SETTINGS="$HOME/.claude/settings.json"
HOOK_CMD="$SCRIPT_DIR/scripts/show.sh"

# 1. Create user config dir
mkdir -p "$CONFIG_DIR/gifs"
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    echo '{ "lang": "auto" }' > "$CONFIG_DIR/config.json"
    echo "Created $CONFIG_DIR/config.json"
else
    echo "User config already exists, skipping"
fi

# 2. Make scripts executable
chmod +x "$SCRIPT_DIR/scripts/show.sh" "$SCRIPT_DIR/scripts/hide.sh"

# 3. Install Python dependencies
uv sync --project "$SCRIPT_DIR"

# 4. Add Claude Code hook
if [ ! -f "$SETTINGS" ]; then
    echo "No $SETTINGS found — skipping hook setup."
    echo "Manually add a UserPromptSubmit hook with command: $HOOK_CMD"
    exit 0
fi

# Use python to safely append hook without clobbering existing hooks
python3 -c "
import json, sys

with open('$SETTINGS') as f:
    s = json.load(f)

hook_cmd = '$HOOK_CMD'

# Check if this exact command is already registered
for group in s.get('hooks', {}).get('UserPromptSubmit', []):
    for h in group.get('hooks', []):
        if h.get('command') == hook_cmd:
            print('Claude Code hook already installed')
            sys.exit(0)

s.setdefault('hooks', {}).setdefault('UserPromptSubmit', []).append({
    'matcher': '',
    'hooks': [{
        'type': 'command',
        'command': hook_cmd,
        'timeout': 15,
        'async': True
    }]
})

with open('$SETTINGS', 'w') as f:
    json.dump(s, f, indent=2)
print('Added UserPromptSubmit hook to $SETTINGS')
"

echo ""
echo "Done! vibe-wellness will show exercise reminders during Claude Code sessions."
echo "Config: $CONFIG_DIR/config.json"
echo "Custom GIFs: $CONFIG_DIR/gifs/"
