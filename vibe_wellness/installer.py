"""Interactive installer for vibe-wellness."""

import json
import shutil
import subprocess
import sys
import termios
import tty
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "vibe-wellness"
SETTINGS = Path.home() / ".claude" / "settings.json"
HOOK_CMD = "vibe-wellness --show"

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
CYAN = "\033[36m"
RESET = "\033[0m"
UP = "\033[A"
CLEAR_LINE = "\033[2K"


def say(msg):
    print(f"{BOLD}{GREEN}==>{RESET} {BOLD}{msg}{RESET}")


def info(msg):
    print(f"  {DIM}{msg}{RESET}")


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


def _handle_key(key, cur, n):
    if key == "\x1b[A":
        return (cur - 1) % n
    elif key == "\x1b[B":
        return (cur + 1) % n
    elif key in ("\x03", "\x04"):
        print()
        sys.exit(0)
    return cur


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
        if key in ("\r", "\n"):
            sys.stdout.write(f"{UP}{CLEAR_LINE}" * n)
            sys.stdout.flush()
            for i, (label, _) in enumerate(options):
                if i == cur:
                    print(f"  {CYAN}>{RESET} {BOLD}{label}{RESET}")
                else:
                    print(f"    {DIM}{label}{RESET}")
            return options[cur][1]
        new = _handle_key(key, cur, n)
        if new != cur:
            cur = new
            sys.stdout.write(f"{UP}{CLEAR_LINE}" * n)
            sys.stdout.flush()
            draw()


def multiselect(options, selected=None):
    cur = 0
    n = len(options)
    if selected is None:
        selected = set(range(n))
    hint_lines = 2

    def draw():
        for i, label in enumerate(options):
            arrow = f"{CYAN}>{RESET}" if i == cur else " "
            check = f"{GREEN}*{RESET}" if i in selected else " "
            style = BOLD if i == cur else DIM
            print(f"  {arrow} [{check}] {style}{label}{RESET}")
        print(f"\n  {DIM}space: toggle  enter: confirm{RESET}")

    draw()
    total = n + hint_lines
    while True:
        key = read_key()
        if key == " ":
            selected ^= {cur}
        elif key in ("\r", "\n"):
            sys.stdout.write(f"{UP}{CLEAR_LINE}" * total)
            sys.stdout.flush()
            for i, label in enumerate(options):
                check = f"{GREEN}*{RESET}" if i in selected else " "
                style = BOLD if i in selected else DIM
                print(f"    [{check}] {style}{label}{RESET}")
            return sorted(selected)
        else:
            new = _handle_key(key, cur, n)
            if new == cur:
                continue
            cur = new
        sys.stdout.write(f"{UP}{CLEAR_LINE}" * total)
        sys.stdout.flush()
        draw()


def main():
    print()
    print(f"{BOLD}  vibe-wellness installer{RESET}")
    print(f"  {DIM}Exercise reminders for Claude Code{RESET}")
    print()

    if not shutil.which("uv"):
        print("uv is required. Install: curl -LsSf https://astral.sh/uv/install.sh | sh")
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

    # Exercise selection (from bundled config)
    from .config import PKG_DIR
    default_config = json.loads((PKG_DIR / "config.json").read_text())
    all_exercises = default_config["exercises"]
    display_key = "zh" if lang == "zh" else "en"
    labels = [ex["name"].get(display_key, ex["name"]["en"]) for ex in all_exercises]

    say("Exercises")
    chosen = multiselect(labels)
    exercises = [all_exercises[i] for i in chosen]
    print()

    # Install via uv tool
    say("Installing vibe-wellness")
    subprocess.run(
        ["uv", "tool", "install", "vibe-wellness", "--python", "3.12", "--force"],
        check=True,
    )

    # User config
    say("Setting up config")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "gifs").mkdir(exist_ok=True)
    config = {"lang": lang, "interval": interval, "exercises": exercises}
    (CONFIG_DIR / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
    info(f"Wrote {CONFIG_DIR / 'config.json'}")

    # Claude Code hook
    if not SETTINGS.exists():
        say("Claude Code settings not found")
        info(f"Manually add a UserPromptSubmit hook:")
        info(f"  command: {HOOK_CMD}")
    else:
        settings = json.loads(SETTINGS.read_text())
        already = False
        for group in settings.get("hooks", {}).get("UserPromptSubmit", []):
            for h in group.get("hooks", []):
                if "vibe-wellness" in h.get("command", ""):
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
                    "command": HOOK_CMD,
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
    info(f"Uninstall:   uv tool uninstall vibe-wellness && rm -rf {CONFIG_DIR}")
    print()
