#!/bin/bash
# Installer for vibe-wellness
# Usage: curl -fsSL https://raw.githubusercontent.com/odysa/vibe-wellness/main/install.sh | bash
set -e

# 1. Install uv if needed
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# 2. Install the package
uv tool install vibe-wellness --force

# 3. Run interactive setup
vibe-wellness
