"""CLI entry point for vibe-wellness."""

import sys


def main():
    if "--install" in sys.argv or not _is_installed():
        from .installer import main as install
        install()
    else:
        from .ui import main as show
        show()


def _is_installed():
    from pathlib import Path
    settings = Path.home() / ".claude" / "settings.json"
    if not settings.exists():
        return False
    import json
    data = json.loads(settings.read_text())
    for group in data.get("hooks", {}).get("UserPromptSubmit", []):
        for h in group.get("hooks", []):
            if "vibe-wellness" in h.get("command", ""):
                return True
    return False
