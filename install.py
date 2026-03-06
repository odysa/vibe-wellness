#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Thin wrapper for: uvx --from git+https://github.com/odysa/vibe-wellness vibe-wellness"""
import subprocess, sys, shutil
if not shutil.which("uv"):
    print("uv is required. Install: curl -LsSf https://astral.sh/uv/install.sh | sh")
    sys.exit(1)
sys.exit(subprocess.call([
    "uvx", "--from", "git+https://github.com/odysa/vibe-wellness", "vibe-wellness"
]))
