"""Guard: single-instance + interval check, then spawn overlay."""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

LOCK_DIR = Path("/tmp/vibe-wellness.lock")
INTERVAL_FILE = Path("/tmp/vibe-wellness-interval")
SEDENTARY_INTERVAL_FILE = Path("/tmp/vibe-wellness-sedentary")


def _acquire_lock():
    """Try to acquire the overlay lock. Returns True on success."""
    try:
        LOCK_DIR.mkdir()
        return True
    except FileExistsError:
        pid_file = LOCK_DIR / "pid"
        if pid_file.exists():
            try:
                os.kill(int(pid_file.read_text().strip()), 0)
                return False  # overlay still running
            except (OSError, ValueError):
                pass
        # Stale lock
        shutil.rmtree(LOCK_DIR, ignore_errors=True)
        try:
            LOCK_DIR.mkdir()
            return True
        except FileExistsError:
            return False


def _interval_due(interval_file, interval):
    """Check if enough time has passed since last trigger."""
    if interval_file.exists():
        try:
            last = int(interval_file.read_text().strip())
            if int(time.time()) - last < interval:
                return False
        except ValueError:
            pass
    return True


def show():
    if not _acquire_lock():
        return

    from .config import load_config
    cfg = load_config()

    # Check sedentary first (independent interval)
    sed_cfg = cfg.get("sedentary", {})
    sed_enabled = sed_cfg.get("enabled", True)
    sed_interval = sed_cfg.get("interval", 1800)

    if sed_enabled and _interval_due(SEDENTARY_INTERVAL_FILE, sed_interval):
        SEDENTARY_INTERVAL_FILE.write_text(str(int(time.time())))
        proc = subprocess.Popen(
            [sys.executable, "-m", "vibe_wellness", "--overlay", "--sedentary"],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        (LOCK_DIR / "pid").write_text(str(proc.pid))
        return

    # Check exercise interval
    interval = cfg.get("interval", 900)
    if _interval_due(INTERVAL_FILE, interval):
        INTERVAL_FILE.write_text(str(int(time.time())))
        proc = subprocess.Popen(
            [sys.executable, "-m", "vibe_wellness", "--overlay"],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        (LOCK_DIR / "pid").write_text(str(proc.pid))
        return

    # Neither due
    shutil.rmtree(LOCK_DIR, ignore_errors=True)
