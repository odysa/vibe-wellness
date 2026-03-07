"""Guard: single-instance + interval check, then spawn overlay."""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

LOCK_DIR = Path("/tmp/vibe-wellness.lock")
INTERVAL_FILE = Path("/tmp/vibe-wellness-interval")


def show():
    # Atomic lock via mkdir
    try:
        LOCK_DIR.mkdir()
    except FileExistsError:
        pid_file = LOCK_DIR / "pid"
        if pid_file.exists():
            try:
                os.kill(int(pid_file.read_text().strip()), 0)
                return  # overlay still running
            except (OSError, ValueError):
                pass
        # Stale lock
        shutil.rmtree(LOCK_DIR, ignore_errors=True)
        try:
            LOCK_DIR.mkdir()
        except FileExistsError:
            return

    # Interval check
    from .config import load_config
    cfg = load_config()
    interval = cfg.get("interval", 900)

    if INTERVAL_FILE.exists():
        try:
            last = int(INTERVAL_FILE.read_text().strip())
            if int(time.time()) - last < interval:
                shutil.rmtree(LOCK_DIR, ignore_errors=True)
                return
        except ValueError:
            pass

    # Write timestamp before spawning to prevent races with concurrent hooks
    INTERVAL_FILE.write_text(str(int(time.time())))

    # Spawn overlay as detached process
    proc = subprocess.Popen(
        [sys.executable, "-m", "vibe_wellness", "--overlay"],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    (LOCK_DIR / "pid").write_text(str(proc.pid))
