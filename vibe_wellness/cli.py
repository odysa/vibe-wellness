"""CLI entry point for vibe-wellness."""

import sys


def main():
    if "--show" in sys.argv:
        from .show import show
        show()
    elif "--overlay" in sys.argv:
        from .ui import main as overlay
        overlay(sedentary="--sedentary" in sys.argv)
    elif "--uninstall" in sys.argv:
        from .uninstall import main as uninstall
        uninstall()
    else:
        from .installer import main as install
        install()
