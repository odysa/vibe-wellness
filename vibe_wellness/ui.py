"""Floating exercise reminder overlay for macOS."""

import atexit
import os
import random
import shutil
import signal
import sys
from pathlib import Path

LOCK_DIR = Path("/tmp/vibe-wellness.lock")
atexit.register(lambda: shutil.rmtree(LOCK_DIR, ignore_errors=True))

# Fix Tcl/Tk paths for venv
_base = Path(sys.base_prefix) / "lib"
for _name, _var in [("tcl8.6", "TCL_LIBRARY"), ("tk8.6", "TK_LIBRARY")]:
    _p = _base / _name
    if _p.exists():
        os.environ.setdefault(_var, str(_p))

import tkinter as tk

from .config import STRINGS, detect_system_lang, load_config, resolve_gif

BG = "#1e1e2e"
FG = "#e0e0f0"
DIM = "#888899"


def load_gif_frames(root, gif_path: Path):
    frames = []
    try:
        i = 0
        while True:
            frames.append(tk.PhotoImage(file=str(gif_path), format=f"gif -index {i}"))
            i += 1
    except tk.TclError:
        pass
    return frames


def label(parent, text, size=16, color=FG, bold=False, **pack_kw):
    weight = "bold" if bold else ""
    lbl = tk.Label(parent, text=text, font=("SF Pro", size, weight), fg=color, bg=BG)
    lbl.pack(**pack_kw)
    return lbl


def create_window(cfg, has_gif):
    root = tk.Tk()
    root.title("")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg=BG)

    w = cfg.get("window_width", 420)
    h = cfg.get("window_height_gif", 520) if has_gif else cfg.get("window_height_no_gif", 280)
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    try:
        root.tk.call("::tk::unsupported::MacWindowStyle", "style", root._w, "plain", "noTitleBar")
    except tk.TclError:
        pass

    return root


def main():
    cfg = load_config()
    lang = cfg.get("lang", "auto")
    if lang == "auto":
        lang = detect_system_lang()
    strings = STRINGS.get(lang, STRINGS["en"])

    ex = random.choice(cfg["exercises"])
    name = ex["name"].get(lang, ex["name"]["en"])
    gif_path = resolve_gif(ex["key"])
    has_gif = gif_path is not None

    root = create_window(cfg, has_gif)
    opacity = cfg.get("opacity", 0.92)
    root.attributes("-alpha", 0.0)

    def dismiss(event=None):
        root.destroy()

    root.bind("<Button-1>", dismiss)
    signal.signal(signal.SIGTERM, lambda *_: dismiss())

    # Countdown phase
    cd_frame = tk.Frame(root, bg=BG)
    cd_frame.pack(fill="both", expand=True)
    label(cd_frame, strings["title"], size=16, color=DIM, pady=(60, 8))
    label(cd_frame, name, size=28, bold=True, pady=(0, 20))
    cd_num = label(cd_frame, "3", size=72, bold=True, color=DIM, expand=True)

    def show_exercise():
        cd_frame.destroy()
        frame = tk.Frame(root, bg=BG, padx=30, pady=20)
        frame.pack(fill="both", expand=True)

        label(frame, strings["title"], size=16, color=DIM, pady=(8, 4))

        if has_gif:
            gif_frames = load_gif_frames(root, gif_path)
            if gif_frames:
                gif_label = tk.Label(frame, bg=BG)
                gif_label.pack(pady=(8, 4))
                idx = [0]
                speed = cfg.get("gif_speed", 140)

                def animate():
                    gif_label.configure(image=gif_frames[idx[0]])
                    idx[0] = (idx[0] + 1) % len(gif_frames)
                    root.after(speed, animate)

                animate()
        else:
            label(frame, "\U0001f3cb\ufe0f", size=56, pady=(4, 0))

        label(frame, name, size=28, bold=True, pady=(4, 0))
        label(frame, strings["dismiss"], size=13, color="#777788", pady=(10, 0))
        root.after(cfg.get("duration", 30) * 1000, dismiss)

    def countdown(n=3):
        if n <= 0:
            show_exercise()
        else:
            cd_num.configure(text=str(n))
            root.after(1000, countdown, n - 1)

    def fade_in(alpha=0.0):
        if alpha <= opacity:
            root.attributes("-alpha", alpha)
            root.after(20, fade_in, alpha + 0.08)
        else:
            countdown()

    fade_in()
    root.mainloop()
