#!/bin/bash
# Bootstrap installer for vibe-wellness
# Usage: curl -fsSL https://raw.githubusercontent.com/odysa/vibe-wellness/main/install.sh | bash
set -e

if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

uvx vibe-wellness@latest
