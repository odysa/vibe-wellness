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
import termios
import tty
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


CYAN = "\033[36m"
UP = "\033[A"
CLEAR_LINE = "\033[2K"


def read_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch += sys.stdin.read(2)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def select(options, default=0):
    cur = default
    n = len(options)

    def draw():
        for i, (label, _) in enumerate(options):
            marker = f"{CYAN}>{RESET}" if i == cur else " "
            style = BOLD if i == cur else DIM
            print(f"  {marker} {style}{label}{RESET}")

    draw()
    while True:
        key = read_key()
        if key == "\x1b[A":  # up
            cur = (cur - 1) % n
        elif key == "\x1b[B":  # down
            cur = (cur + 1) % n
        elif key in ("\r", "\n"):  # enter
            # Move cursor up and redraw with selection
            sys.stdout.write(f"{UP}{CLEAR_LINE}" * n)
            sys.stdout.flush()
            for i, (label, _) in enumerate(options):
                if i == cur:
                    print(f"  {CYAN}>{RESET} {BOLD}{label}{RESET}")
                else:
                    print(f"    {DIM}{label}{RESET}")
            return options[cur][1]
        elif key in ("\x03", "\x04"):  # ctrl-c / ctrl-d
            print()
            sys.exit(0)
        else:
            continue
        # Redraw
        sys.stdout.write(f"{UP}{CLEAR_LINE}" * n)
        sys.stdout.flush()
        draw()


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
    lang = select([
        ("English", "en"),
        ("中文", "zh"),
        ("Auto-detect", "auto"),
    ], default=2)
    print()

    # Interval
    say("Reminder interval")
    interval = select([
        ("10 min", 600),
        ("15 min", 900),
        ("20 min", 1200),
        ("30 min", 1800),
    ], default=1)
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
