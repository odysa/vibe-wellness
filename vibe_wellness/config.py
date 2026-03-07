"""Configuration loading and i18n for vibe-wellness."""

import json
import subprocess
from pathlib import Path

PKG_DIR = Path(__file__).parent
DEFAULT_CONFIG = PKG_DIR / "config.json"
GIF_DIR = PKG_DIR / "gifs"

USER_DIR = Path.home() / ".config" / "vibe-wellness"
USER_CONFIG = USER_DIR / "config.json"
USER_GIF_DIR = USER_DIR / "gifs"

STRINGS = {
    "en": {"title": "Time to move!", "dismiss": "click to dismiss"},
    "zh": {"title": "动起来！", "dismiss": "点击关闭"},
}

SEDENTARY_STRINGS = {
    "en": {
        "title": "Sedentary Alert",
        "message": "You've been sitting too long!\nStand up and stretch.",
        "dismiss": "click to dismiss",
    },
    "zh": {
        "title": "久坐提醒",
        "message": "坐太久了！\n站起来活动一下吧",
        "dismiss": "点击关闭",
    },
}


def detect_system_lang():
    """Detect macOS system language, return 'en' or 'zh' etc."""
    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleLocale"],
            capture_output=True, text=True, timeout=2,
        )
        locale = result.stdout.strip().lower()
        if locale.startswith("zh"):
            return "zh"
        return locale.split("_")[0]
    except Exception:
        return "en"


def load_config():
    """Load user config from ~/.config/vibe-wellness/, fallback to bundled default."""
    with open(DEFAULT_CONFIG) as f:
        cfg = json.load(f)
    if USER_CONFIG.exists():
        with open(USER_CONFIG) as f:
            user = json.load(f)
        cfg.update(user)
    return cfg


def resolve_gif(key):
    """Return GIF path for an exercise key, preferring user dir over bundled."""
    user_gif = USER_GIF_DIR / f"{key}.gif"
    if user_gif.exists():
        return user_gif
    bundled = GIF_DIR / f"{key}.gif"
    if bundled.exists():
        return bundled
    return None
