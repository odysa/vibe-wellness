"""Uninstaller for vibe-wellness."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "vibe-wellness"
HOOK_DIR = Path.home() / ".claude" / "hooks" / "vibe-wellness"
SETTINGS = Path.home() / ".claude" / "settings.json"

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"


def say(msg):
    print(f"{BOLD}{GREEN}==>{RESET} {BOLD}{msg}{RESET}")


def info(msg):
    print(f"  {DIM}{msg}{RESET}")


def main():
    print()
    print(f"{BOLD}  vibe-wellness uninstaller{RESET}")
    print()

    # Remove Claude Code hooks
    if SETTINGS.exists():
        say("Removing Claude Code hooks")
        settings = json.loads(SETTINGS.read_text())
        changed = False
        for event in list(settings.get("hooks", {})):
            groups = settings["hooks"][event]
            filtered = []
            for group in groups:
                hooks = [h for h in group.get("hooks", []) if "vibe-wellness" not in h.get("command", "")]
                if hooks:
                    group["hooks"] = hooks
                    filtered.append(group)
            if len(filtered) != len(groups):
                settings["hooks"][event] = filtered
                changed = True
        if changed:
            SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
            info("Removed hooks from settings.json")
        else:
            info("No hooks found")

    # Remove hook script
    if HOOK_DIR.exists():
        say("Removing hook script")
        shutil.rmtree(HOOK_DIR)
        info(f"Removed {HOOK_DIR}")

    # Remove config
    if CONFIG_DIR.exists():
        say("Removing config")
        shutil.rmtree(CONFIG_DIR)
        info(f"Removed {CONFIG_DIR}")

    # Remove tmp files
    say("Cleaning up")
    for p in ["/tmp/vibe-wellness.lock", "/tmp/vibe-wellness-interval"]:
        path = Path(p)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    info("Removed temp files")

    # Uninstall tool
    say("Uninstalling tool")
    subprocess.run(["uv", "tool", "uninstall", "vibe-wellness"], check=False)

    print()
    print(f"{BOLD}{GREEN}  Done!{RESET} vibe-wellness has been removed.")
    print()
