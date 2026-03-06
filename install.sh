#!/bin/bash
# Interactive installer for vibe-wellness
# Usage: curl -fsSL https://raw.githubusercontent.com/odysa/vibe-wellness/main/install.sh | bash
set -e

REPO="https://github.com/odysa/vibe-wellness.git"
INSTALL_DIR="$HOME/.vibe-wellness"
CONFIG_DIR="$HOME/.config/vibe-wellness"
SETTINGS="$HOME/.claude/settings.json"

# Colors
bold="\033[1m"
dim="\033[2m"
green="\033[32m"
cyan="\033[36m"
reset="\033[0m"

say() { echo -e "${bold}${green}==>${reset} ${bold}$1${reset}"; }
info() { echo -e "  ${dim}$1${reset}"; }

echo ""
echo -e "${bold}  vibe-wellness installer${reset}"
echo -e "  ${dim}Exercise reminders for Claude Code${reset}"
echo ""

# --- Check dependencies ---
if ! command -v uv &>/dev/null; then
    echo "uv is required but not found. Install it:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

if ! command -v git &>/dev/null; then
    echo "git is required but not found."
    exit 1
fi

# --- Language ---
say "Language / 语言"
echo "  1) English"
echo "  2) 中文"
echo "  3) Auto-detect"
echo ""
printf "  Choose [3]: "
read -r lang_choice
case "$lang_choice" in
    1) LANG_VAL="en" ;;
    2) LANG_VAL="zh" ;;
    *) LANG_VAL="auto" ;;
esac
echo ""

# --- Interval ---
say "Reminder interval"
echo "  1) 10 min"
echo "  2) 15 min (default)"
echo "  3) 20 min"
echo "  4) 30 min"
echo ""
printf "  Choose [2]: "
read -r interval_choice
case "$interval_choice" in
    1) INTERVAL=600 ;;
    3) INTERVAL=1200 ;;
    4) INTERVAL=1800 ;;
    *) INTERVAL=900 ;;
esac
echo ""

# --- Clone / Update ---
say "Installing to $INSTALL_DIR"
if [ -d "$INSTALL_DIR/.git" ]; then
    info "Updating existing installation..."
    git -C "$INSTALL_DIR" pull --quiet
else
    rm -rf "$INSTALL_DIR"
    git clone --quiet "$REPO" "$INSTALL_DIR"
fi

# --- Dependencies ---
say "Installing dependencies"
uv sync --project "$INSTALL_DIR" --quiet

# --- User config ---
say "Setting up config"
mkdir -p "$CONFIG_DIR/gifs"
cat > "$CONFIG_DIR/config.json" <<CONF
{
  "lang": "$LANG_VAL",
  "interval": $INTERVAL
}
CONF
info "Wrote $CONFIG_DIR/config.json"

# --- Scripts ---
chmod +x "$INSTALL_DIR/scripts/show.sh" "$INSTALL_DIR/scripts/hide.sh"

# --- Claude Code hook ---
HOOK_CMD="$INSTALL_DIR/scripts/show.sh"

if [ ! -f "$SETTINGS" ]; then
    say "Claude Code settings not found"
    info "Manually add a UserPromptSubmit hook:"
    info "  command: $HOOK_CMD"
else
    python3 -c "
import json, sys

with open('$SETTINGS') as f:
    s = json.load(f)

hook_cmd = '$HOOK_CMD'

for group in s.get('hooks', {}).get('UserPromptSubmit', []):
    for h in group.get('hooks', []):
        if h.get('command') == hook_cmd:
            print('  Hook already installed, skipping')
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
print('  Added UserPromptSubmit hook')
"
fi

# --- Done ---
echo ""
echo -e "${bold}${green}  Done!${reset}"
echo ""
info "Reminders will appear every $(( INTERVAL / 60 )) min during Claude Code sessions."
info "Config:      $CONFIG_DIR/config.json"
info "Custom GIFs: $CONFIG_DIR/gifs/"
info "Uninstall:   rm -rf $INSTALL_DIR $CONFIG_DIR"
echo ""
