"""Interactive installer for vibe-wellness."""

import json
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

    for cmd in ("uv", "git"):
        if not shutil.which(cmd):
            print(f"{cmd} is required but not found.")
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

    # Exercise selection
    default_config = json.loads((INSTALL_DIR / "vibe_wellness" / "config.json").read_text())
    all_exercises = default_config["exercises"]
    display_key = "zh" if lang == "zh" else "en"
    labels = [ex["name"].get(display_key, ex["name"]["en"]) for ex in all_exercises]

    say("Exercises")
    chosen = multiselect(labels)
    exercises = [all_exercises[i] for i in chosen]
    print()

    # User config
    say("Setting up config")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "gifs").mkdir(exist_ok=True)
    config = {"lang": lang, "interval": interval, "exercises": exercises}
    (CONFIG_DIR / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
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
