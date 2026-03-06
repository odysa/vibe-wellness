"""CLI entry point for vibe-wellness."""


def main():
    from .installer import main as install
    install()
