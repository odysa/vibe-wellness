# vibe-wellness

Exercise reminder overlay for macOS. Pops up during Claude Code sessions to remind you to move.

![overlay](https://img.shields.io/badge/macOS-overlay-blue) ![python](https://img.shields.io/badge/python-3.12+-green) ![PyPI](https://img.shields.io/pypi/v/vibe-wellness)

## What it does

A floating overlay window appears periodically when you're using Claude Code:

1. 3-second countdown with exercise name
2. Animated stick figure GIF showing the exercise
3. Auto-dismisses after 30 seconds (or click to dismiss)

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/odysa/vibe-wellness/main/install.sh | bash
```

The installer will:
1. Install [uv](https://docs.astral.sh/uv/) (if not found)
2. Install `vibe-wellness` from PyPI
3. Run the interactive setup wizard

### Manual install

If you prefer to install manually:

```bash
uv tool install vibe-wellness
vibe-wellness          # run setup wizard
```

## Exercises

| Key | English | 中文 | GIF |
|-----|---------|------|-----|
| `kegels` | Kegels | 提肛 | included |
| `drink_water` | Drink Water | 喝水 | included |
| `squats` | Squats | 深蹲 | included |
| `wall_pushups` | Wall Push-ups | 靠墙俯卧撑 | included |
| `neck_rolls` | Neck Rolls | 颈椎运动 | included |

## Configuration

Edit `~/.config/vibe-wellness/config.json`, or re-run `vibe-wellness` to launch the setup wizard.

```json
{
  "lang": "zh",
  "interval": 900
}
```

| Key | Default | Description |
|-----|---------|-------------|
| `lang` | `"auto"` | Language: `"en"`, `"zh"`, or `"auto"` (detect system) |
| `interval` | `900` | Seconds between reminders |
| `duration` | `30` | Overlay display time in seconds |
| `opacity` | `0.92` | Window opacity (0.0 - 1.0) |
| `exercises` | (built-in) | Custom exercise list (see below) |

### Custom exercises

Add exercises in your config. They merge with defaults by `key`:

```json
{
  "exercises": [
    { "key": "stretching", "name": { "en": "Stretch", "zh": "拉伸" } }
  ]
}
```

### Custom GIFs

Drop a `{key}.gif` in `~/.config/vibe-wellness/gifs/` to use your own animation for any exercise.

## Uninstall

```bash
vibe-wellness --uninstall
```

Or manually:

```bash
uv tool uninstall vibe-wellness
rm -rf ~/.config/vibe-wellness
```

Then remove the `vibe-wellness` hook entry from `~/.claude/settings.json`.

## Project structure

```
install.sh                # Installer: installs package + runs setup
vibe_wellness/
  cli.py                  # Entry point: --show / --overlay / --uninstall / setup
  installer.py            # Interactive setup wizard (TUI)
  show.py                 # Single-instance guard + interval check
  ui.py                   # Overlay window (tkinter)
  config.py               # Config loading, i18n, language detection
  config.json             # Default config + exercises
  uninstall.py            # Clean removal
  gifs/                   # Bundled exercise GIFs
```
