#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Interactive installer for vibe-wellness.

Usage: uv run https://raw.githubusercontent.com/odysa/vibe-wellness/main/install.py
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = "https://github.com/odysa/vibe-wellness.git"
INSTALL_DIR = Path.home() / ".vibe-wellness"
CONFIG_DIR = Path.home() / ".config" / "vibe-wellness"
SETTINGS = Path.home() / ".claude" / "settings.json"

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
RESET = "\033[0m"


def say(msg):
    print(f"{BOLD}{GREEN}==>{RESET} {BOLD}{msg}{RESET}")


def info(msg):
    print(f"  {DIM}{msg}{RESET}")


def ask(prompt, options, default):
    for i, (label, _) in enumerate(options, 1):
        print(f"  {i}) {label}")
    print()
    choice = input(f"  {prompt} [{default}]: ").strip()
    try:
        idx = int(choice) - 1
        return options[idx][1]
    except (ValueError, IndexError):
        return options[default - 1][1]


def main():
    print()
    print(f"{BOLD}  vibe-wellness installer{RESET}")
    print(f"  {DIM}Exercise reminders for Claude Code{RESET}")
    print()

    # Check dependencies
    if not shutil.which("uv"):
        print("uv is required. Install: curl -LsSf https://astral.sh/uv/install.sh | sh")
        sys.exit(1)
    if not shutil.which("git"):
        print("git is required but not found.")
        sys.exit(1)

    # Language
    say("Language / 语言")
    lang = ask("Choose", [
        ("English", "en"),
        ("中文", "zh"),
        ("Auto-detect", "auto"),
    ], default=3)
    print()

    # Interval
    say("Reminder interval")
    interval = ask("Choose", [
        ("10 min", 600),
        ("15 min (default)", 900),
        ("20 min", 1200),
        ("30 min", 1800),
    ], default=2)
    print()

    # Clone / Update
    say(f"Installing to {INSTALL_DIR}")
    if (INSTALL_DIR / ".git").is_dir():
        info("Updating existing installation...")
        subprocess.run(["git", "-C", str(INSTALL_DIR), "pull", "--quiet"], check=True)
    else:
        if INSTALL_DIR.exists():
            shutil.rmtree(INSTALL_DIR)
        subprocess.run(["git", "clone", "--quiet", REPO, str(INSTALL_DIR)], check=True)

    # Dependencies
    say("Installing dependencies")
    subprocess.run(["uv", "sync", "--project", str(INSTALL_DIR), "--quiet"], check=True)

    # User config
    say("Setting up config")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "gifs").mkdir(exist_ok=True)
    config = {"lang": lang, "interval": interval}
    (CONFIG_DIR / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    info(f"Wrote {CONFIG_DIR / 'config.json'}")

    # Scripts
    for script in ["show.sh", "hide.sh"]:
        (INSTALL_DIR / "scripts" / script).chmod(0o755)

    # Claude Code hook
    hook_cmd = str(INSTALL_DIR / "scripts" / "show.sh")

    if not SETTINGS.exists():
        say("Claude Code settings not found")
        info(f"Manually add a UserPromptSubmit hook:")
        info(f"  command: {hook_cmd}")
    else:
        settings = json.loads(SETTINGS.read_text())
        # Check if already installed
        already = False
        for group in settings.get("hooks", {}).get("UserPromptSubmit", []):
            for h in group.get("hooks", []):
                if h.get("command") == hook_cmd:
                    already = True
                    break

        if already:
            info("Hook already installed, skipping")
        else:
            hooks = settings.setdefault("hooks", {})
            hooks.setdefault("UserPromptSubmit", []).append({
                "matcher": "",
                "hooks": [{
                    "type": "command",
                    "command": hook_cmd,
                    "timeout": 15,
                    "async": True,
                }],
            })
            SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
            info("Added UserPromptSubmit hook")

    # Done
    print()
    print(f"{BOLD}{GREEN}  Done!{RESET}")
    print()
    info(f"Reminders will appear every {interval // 60} min during Claude Code sessions.")
    info(f"Config:      {CONFIG_DIR / 'config.json'}")
    info(f"Custom GIFs: {CONFIG_DIR / 'gifs/'}")
    info(f"Uninstall:   rm -rf {INSTALL_DIR} {CONFIG_DIR}")
    print()


if __name__ == "__main__":
    main()
