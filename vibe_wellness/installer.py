"""Interactive setup wizard for vibe-wellness."""

import json
import shutil
import subprocess
import sys
import termios
import tty
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "vibe-wellness"
SETTINGS = Path.home() / ".claude" / "settings.json"
BIN_PATH = Path.home() / ".local" / "bin" / "vibe-wellness"
HOOK_CMD = str(BIN_PATH) + " --show"


def hook_installed(event):
    if not SETTINGS.exists():
        return False
    settings = json.loads(SETTINGS.read_text())
    for group in settings.get("hooks", {}).get(event, []):
        for h in group.get("hooks", []):
            if "vibe-wellness" in h.get("command", ""):
                return True
    return False

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
CYAN = "\033[36m"
RESET = "\033[0m"
UP = "\033[A"
CLEAR_LINE = "\033[2K"

I18N = {
    "en": {
        "subtitle": "Exercise reminders for Claude Code",
        "interval": "Reminder interval",
        "exercises": "Exercises",
        "installing": "Installing vibe-wellness",
        "config": "Setting up config",
        "wrote": "Wrote",
        "hook_title": "Claude Code hook",
        "hook_pick": "When should reminders appear?",
        "hook_already": "Hook already installed, skipping",
        "hook_added": "Added hook",
        "hook_not_found": "Claude Code settings not found",
        "hook_manual": "Manually add a hook with command:",
        "verify": "Verifying setup",
        "check_tool": "vibe-wellness command available",
        "check_config": "Config file exists",
        "check_hook": "Claude Code hook registered ({})",
        "done": "All good! Ready to go.",
        "done_partial": "Installed with warnings — check above.",
        "remind_every": "Reminders will appear every {} min during Claude Code sessions.",
        "uninstall": "Uninstall: vibe-wellness --uninstall",
    },
    "zh": {
        "subtitle": "Claude Code 运动提醒",
        "interval": "提醒间隔",
        "exercises": "运动项目",
        "installing": "安装 vibe-wellness",
        "config": "配置",
        "wrote": "已写入",
        "hook_title": "Claude Code 钩子",
        "hook_pick": "什么时候提醒？",
        "hook_already": "钩子已安装，跳过",
        "hook_added": "已添加钩子",
        "hook_not_found": "未找到 Claude Code 配置",
        "hook_manual": "请手动添加钩子命令：",
        "verify": "验证安装",
        "check_tool": "vibe-wellness 命令可用",
        "check_config": "配置文件已创建",
        "check_hook": "Claude Code 钩子已注册 ({})",
        "done": "一切就绪！",
        "done_partial": "安装完成，但有警告 — 请检查上方信息。",
        "remind_every": "每 {} 分钟在 Claude Code 中提醒运动。",
        "uninstall": "卸载：vibe-wellness --uninstall",
    },
}

HOOKS = {
    "en": [
        ("UserPromptSubmit — When you send a message (while Claude thinks)", "UserPromptSubmit"),
        ("Stop — When Claude finishes responding", "Stop"),
        ("Notification — When Claude sends a notification", "Notification"),
    ],
    "zh": [
        ("UserPromptSubmit — 发送消息时（Claude 思考时）", "UserPromptSubmit"),
        ("Stop — Claude 回复完成时", "Stop"),
        ("Notification — Claude 发送通知时", "Notification"),
    ],
}


def say(msg):
    print(f"{BOLD}{GREEN}==>{RESET} {BOLD}{msg}{RESET}")


def info(msg):
    print(f"  {DIM}{msg}{RESET}")


IS_TTY = sys.stdin.isatty()


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
    if not IS_TTY:
        for i, (label, _) in enumerate(options):
            marker = ">" if i == default else " "
            print(f"  {marker} {label}")
        choice = input(f"  [{default + 1}]: ").strip()
        try:
            return options[int(choice) - 1][1]
        except (ValueError, IndexError):
            return options[default][1]

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
    n = len(options)
    if selected is None:
        selected = set(range(n))

    if not IS_TTY:
        for i, label in enumerate(options):
            check = "*" if i in selected else " "
            print(f"  [{check}] {i + 1}. {label}")
        choice = input(f"  Toggle (e.g. 1,3) or enter for all: ").strip()
        if choice:
            for num in choice.split(","):
                try:
                    selected ^= {int(num.strip()) - 1}
                except (ValueError, IndexError):
                    pass
        return sorted(selected)

    cur = 0
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
    print(f"{BOLD}  vibe-wellness setup{RESET}")
    print()

    # Language (always bilingual)
    say("Language / 语言")
    lang = select([
        ("English", "en"),
        ("中文", "zh"),
        ("Auto-detect / 自动检测", "auto"),
    ], default=2)

    # Resolve display language
    if lang == "auto":
        from .config import detect_system_lang
        display_lang = detect_system_lang()
    else:
        display_lang = lang
    t = I18N.get(display_lang, I18N["en"])

    print()
    info(t["subtitle"])
    print()

    # Interval
    say(t["interval"])
    interval = select([
        ("10 min", 600),
        ("15 min", 900),
        ("20 min", 1200),
        ("30 min", 1800),
        ("Custom / 自定义", "custom"),
    ], default=1)
    if interval == "custom":
        try:
            interval = int(input(f"  {DIM}Seconds / 秒: {RESET}").strip())
        except (ValueError, EOFError):
            interval = 900
    print()

    # Exercise selection
    from .config import PKG_DIR
    default_config = json.loads((PKG_DIR / "config.json").read_text())
    all_exercises = default_config["exercises"]
    labels = [ex["name"].get(display_lang, ex["name"]["en"]) for ex in all_exercises]

    say(t["exercises"])
    chosen = multiselect(labels)
    exercises = [all_exercises[i] for i in chosen]
    print()

    # Hook selection
    say(t["hook_pick"])
    hook_options = HOOKS.get(display_lang, HOOKS["en"])
    hook_event = select(hook_options, default=0)
    print()

    # Install binary if not already present (e.g. running via uvx)
    if not BIN_PATH.exists() and shutil.which("uv"):
        say(t.get("installing", "Installing vibe-wellness"))
        subprocess.run(
            ["uv", "tool", "install", "vibe-wellness", "--force"],
            check=True,
        )
        print()

    # User config
    say(t["config"])
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "gifs").mkdir(exist_ok=True)
    config = {"lang": lang, "interval": interval, "exercises": exercises}
    (CONFIG_DIR / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
    info(f"{t['wrote']} {CONFIG_DIR / 'config.json'}")

    # Claude Code hook
    say(t["hook_title"])
    if not SETTINGS.exists():
        info(t["hook_not_found"])
        info(f"{t['hook_manual']} {HOOK_CMD}")
    else:
        settings = json.loads(SETTINGS.read_text())
        already = False
        for group in settings.get("hooks", {}).get(hook_event, []):
            for h in group.get("hooks", []):
                if "vibe-wellness" in h.get("command", ""):
                    already = True
                    break

        if already:
            # Update old hooks that use short command to full path
            updated = False
            for group in settings.get("hooks", {}).get(hook_event, []):
                for h in group.get("hooks", []):
                    cmd = h.get("command", "")
                    if "vibe-wellness" in cmd and cmd != HOOK_CMD:
                        h["command"] = HOOK_CMD
                        updated = True
            if updated:
                SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
                info(f"{t['hook_added']} ({hook_event})")
            else:
                info(t["hook_already"])
        else:
            hooks = settings.setdefault("hooks", {})
            hooks.setdefault(hook_event, []).append({
                "matcher": "",
                "hooks": [{
                    "type": "command",
                    "command": HOOK_CMD,
                    "timeout": 15,
                    "async": True,
                }],
            })
            SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
            info(f"{t['hook_added']} ({hook_event})")

    # Verify
    say(t["verify"])
    checks = [
        (BIN_PATH.exists() or shutil.which("vibe-wellness") is not None, t["check_tool"]),
        ((CONFIG_DIR / "config.json").exists(), t["check_config"]),
        (hook_installed(hook_event), t["check_hook"].format(hook_event)),
    ]
    all_ok = True
    for ok, label in checks:
        mark = f"{GREEN}*{RESET}" if ok else f"\033[31mx{RESET}"
        print(f"  [{mark}] {label}")
        if not ok:
            all_ok = False

    # Done
    print()
    if all_ok:
        print(f"{BOLD}{GREEN}  {t['done']}{RESET}")
    else:
        print(f"{BOLD}\033[31m  {t['done_partial']}{RESET}")
    print()
    if interval >= 60:
        info(t["remind_every"].format(interval // 60))
    else:
        info(f"Reminders every {interval}s")
    info(f"Config: {CONFIG_DIR / 'config.json'}")
    info(t["uninstall"])
    print()
