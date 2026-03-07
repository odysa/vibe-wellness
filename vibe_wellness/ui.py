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

# Fix Tcl/Tk paths for venv (supports Tcl/Tk 8.6 and 9.0)
_base = Path(sys.base_prefix) / "lib"
for _prefix, _var in [("tcl", "TCL_LIBRARY"), ("tk", "TK_LIBRARY")]:
    for _ver in ["9.0", "8.6"]:
        _p = _base / f"{_prefix}{_ver}"
        if _p.exists():
            os.environ.setdefault(_var, str(_p))
            break

# ObjC runtime helpers for macOS window management
import ctypes, ctypes.util
try:
    _objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
    _objc.objc_getClass.restype = ctypes.c_void_p
    _objc.sel_registerName.restype = ctypes.c_void_p
    _objc.objc_msgSend.restype = ctypes.c_void_p

    def _sel(name):
        return _objc.sel_registerName(name.encode())

    def _msg(obj, selector, *args):
        _objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p] + [type(a) for a in args]
        _objc.objc_msgSend.restype = ctypes.c_void_p
        return _objc.objc_msgSend(obj, _sel(selector), *args)

    # Hide dock icon and menu bar (accessory mode)
    _app = _msg(_objc.objc_getClass(b"NSApplication"), "sharedApplication")
    _msg(_app, "setActivationPolicy:", ctypes.c_int64(1))
    _HAS_OBJC = True
except Exception:
    _HAS_OBJC = False


def _make_borderless():
    """Set all NSWindows to borderless (styleMask=0) to remove title bar dots."""
    if not _HAS_OBJC:
        return
    try:
        app = _msg(_objc.objc_getClass(b"NSApplication"), "sharedApplication")
        windows = _msg(app, "windows")
        _objc.objc_msgSend.restype = ctypes.c_uint64
        _objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        n = _objc.objc_msgSend(windows, _sel("count"))
        for i in range(n):
            w = _msg(windows, "objectAtIndex:", ctypes.c_uint64(i))
            _msg(w, "setStyleMask:", ctypes.c_uint64(0))
    except Exception:
        pass

import tkinter as tk

from .config import SEDENTARY_STRINGS, STRINGS, detect_system_lang, load_config, resolve_gif

# Colors — soft dark theme
BG = "#1a1b2e"
CARD = "#242540"
FG = "#e8e8f0"
DIM = "#6e6e8a"
ACCENT = "#7c8aff"
BORDER = "#333456"
PROGRESS_BG = "#2a2b4a"
RADIUS = 20


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


def rounded_rect(canvas, x1, y1, x2, y2, r, **kw):
    """Draw a rounded rectangle on a canvas."""
    points = [
        x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1,
        x2, y1, x2, y1 + r, x2, y1 + r, x2, y2 - r,
        x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2,
        x1 + r, y2, x1 + r, y2, x1, y2, x1, y2 - r,
        x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kw)


def get_main_display_size(root):
    """Get main display size via CoreGraphics (handles multi-monitor)."""
    try:
        import ctypes, ctypes.util
        cg = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreGraphics"))

        class CGRect(ctypes.Structure):
            class CGPoint(ctypes.Structure):
                _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]
            class CGSize(ctypes.Structure):
                _fields_ = [("width", ctypes.c_double), ("height", ctypes.c_double)]
            _fields_ = [("origin", CGPoint), ("size", CGSize)]

        cg.CGMainDisplayID.restype = ctypes.c_uint32
        cg.CGDisplayBounds.restype = CGRect
        cg.CGDisplayBounds.argtypes = [ctypes.c_uint32]
        rect = cg.CGDisplayBounds(cg.CGMainDisplayID())
        return int(rect.size.width), int(rect.size.height)
    except Exception:
        return root.winfo_screenwidth(), root.winfo_screenheight()


def create_window(cfg, has_gif):
    root = tk.Tk()
    root.title("")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg=BG)

    w = cfg.get("window_width", 400)
    h = cfg.get("window_height_gif", 500) if has_gif else cfg.get("window_height_no_gif", 260)

    sw, sh = get_main_display_size(root)
    x = (sw - w) // 2
    y = (sh - h) // 2
    # Set size first, then position after update — fixes overrideredirect on macOS
    root.geometry(f"{w}x{h}")
    root.update_idletasks()
    root.geometry(f"+{x}+{y}")

    # Remove title bar dots (set NSWindow to borderless)
    root.update()
    _make_borderless()

    return root, w, h


def _show_overlay(root, win_w, win_h, cfg, title, name, gif_path, dismiss_text, duration, opacity, small_name=False):
    """Shared overlay UI for both exercise and sedentary modes."""
    has_gif = gif_path is not None
    root.attributes("-alpha", 0.0)

    def dismiss(event=None):
        root.destroy()

    root.bind("<Button-1>", dismiss)
    signal.signal(signal.SIGTERM, lambda *_: dismiss())

    # Background canvas with rounded rect
    bg_canvas = tk.Canvas(root, width=win_w, height=win_h, bg=BG,
                          highlightthickness=0, bd=0)
    bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
    rounded_rect(bg_canvas, 4, 4, win_w - 4, win_h - 4, RADIUS,
                 fill=CARD, outline=BORDER, width=1.5)

    # --- Countdown phase ---
    cd_frame = tk.Frame(root, bg=CARD)
    cd_frame.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(cd_frame, text=title, font=("SF Pro", 14),
             fg=ACCENT, bg=CARD).pack(pady=(40, 6))

    name_font = ("SF Pro", 18) if small_name else ("SF Pro", 26, "bold")
    tk.Label(cd_frame, text=name, font=name_font,
             fg=FG, bg=CARD, wraplength=win_w - 60, justify="center").pack(pady=(0, 24))

    cd_num = tk.Label(cd_frame, text="3", font=("SF Pro", 64, "bold"),
                      fg=DIM, bg=CARD)
    cd_num.pack(pady=(0, 40))

    def show_content():
        cd_frame.destroy()

        frame = tk.Frame(root, bg=CARD)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text=title, font=("SF Pro", 14),
                 fg=ACCENT, bg=CARD).pack(pady=(16, 4))

        if has_gif:
            gif_frames = load_gif_frames(root, gif_path)
            if gif_frames:
                gif_label = tk.Label(frame, bg=CARD, bd=0)
                gif_label.pack(pady=(8, 8))
                idx = [0]
                speed = cfg.get("gif_speed", 140)

                def animate():
                    gif_label.configure(image=gif_frames[idx[0]])
                    idx[0] = (idx[0] + 1) % len(gif_frames)
                    root.after(speed, animate)

                animate()
        else:
            tk.Label(frame, text="\U0001f9d8", font=("SF Pro", 52),
                     bg=CARD).pack(pady=(8, 4))

        content_name_font = ("SF Pro", 16) if small_name else ("SF Pro", 24, "bold")
        tk.Label(frame, text=name, font=content_name_font,
                 fg=FG, bg=CARD, wraplength=win_w - 60, justify="center").pack(pady=(4, 8))

        # Progress bar
        bar_w = 200
        bar_h = 4
        bar_canvas = tk.Canvas(frame, width=bar_w, height=bar_h,
                               bg=CARD, highlightthickness=0, bd=0)
        bar_canvas.pack(pady=(8, 4))
        bar_canvas.create_rectangle(0, 0, bar_w, bar_h, fill=PROGRESS_BG, outline="")
        bar_fill = bar_canvas.create_rectangle(0, 0, bar_w, bar_h,
                                               fill=ACCENT, outline="")

        elapsed = [0]
        total_ms = duration * 1000

        def tick_bar():
            elapsed[0] += 50
            frac = max(0, 1 - elapsed[0] / total_ms)
            bar_canvas.coords(bar_fill, 0, 0, bar_w * frac, bar_h)
            if elapsed[0] < total_ms:
                root.after(50, tick_bar)

        tick_bar()

        tk.Label(frame, text=dismiss_text, font=("SF Pro", 12),
                 fg=DIM, bg=CARD).pack(pady=(8, 16))

        root.after(total_ms, dismiss)

    def countdown(n=3):
        if n <= 0:
            show_content()
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


def main(sedentary=False):
    cfg = load_config()
    lang = cfg.get("lang", "auto")
    if lang == "auto":
        lang = detect_system_lang()
    opacity = cfg.get("opacity", 0.95)
    duration = cfg.get("duration", 30)

    if sedentary:
        sed_strings = SEDENTARY_STRINGS.get(lang, SEDENTARY_STRINGS["en"])
        title = sed_strings["title"]
        name = sed_strings["message"]
        dismiss_text = sed_strings["dismiss"]
        gif_path = resolve_gif("sedentary")
        has_gif = gif_path is not None
        root, win_w, win_h = create_window(cfg, has_gif)
        _show_overlay(root, win_w, win_h, cfg, title, name, gif_path, dismiss_text, duration, opacity, small_name=True)
    else:
        strings = STRINGS.get(lang, STRINGS["en"])
        ex = random.choice(cfg["exercises"])
        name = ex["name"].get(lang, ex["name"]["en"])
        gif_path = resolve_gif(ex["key"])
        has_gif = gif_path is not None
        root, win_w, win_h = create_window(cfg, has_gif)
        _show_overlay(root, win_w, win_h, cfg, strings["title"], name, gif_path, strings["dismiss"], duration, opacity)
