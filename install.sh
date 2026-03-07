#!/bin/bash
# Installer for vibe-wellness
# Usage: curl -fsSL https://raw.githubusercontent.com/odysa/vibe-wellness/main/install.sh | bash
set -e

# Ensure ~/.local/bin is in PATH (uv installs tools here)
export PATH="$HOME/.local/bin:$PATH"

# 1. Install uv if needed
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# 2. Install the package (--no-cache to get latest version)
uv tool install vibe-wellness@latest --force --no-cache

# 3. Verify the binary is accessible
if ! command -v vibe-wellness &>/dev/null; then
    echo "Error: vibe-wellness not found in PATH."
    echo "Add ~/.local/bin to your PATH and try again:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    exit 1
fi

# 4. Run interactive setup (redirect stdin from /dev/tty for curl | bash)
vibe-wellness </dev/tty
