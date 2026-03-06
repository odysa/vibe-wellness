# vibe-wellness

Exercise reminder overlay for macOS. Pops up during Claude Code sessions to remind you to move.

![overlay](https://img.shields.io/badge/macOS-overlay-blue) ![python](https://img.shields.io/badge/python-3.12+-green)

## What it does

A floating overlay window appears every 15 minutes when you're using Claude Code:

1. 3-second countdown with exercise name
2. Animated stick figure GIF showing the exercise
3. Auto-dismisses after 30 seconds (or click to dismiss)

Default exercises (desk-friendly):
- Kegels / 提肛
- Drink Water / 喝水
- Squats / 深蹲
- Wall Push-ups / 靠墙俯卧撑
- Neck Rolls / 颈椎运动

## Install

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
uv run https://raw.githubusercontent.com/odysa/vibe-wellness/main/install.py
```

Or with curl:

```bash
curl -fsSL https://raw.githubusercontent.com/odysa/vibe-wellness/main/install.sh | bash
```

The interactive installer will:
- Ask your preferred language and reminder interval
- Clone to `~/.vibe-wellness/`
- Install dependencies via `uv sync`
- Add a `UserPromptSubmit` hook to `~/.claude/settings.json`

## Usage

The overlay triggers automatically via Claude Code hooks. You can also test manually:

```bash
make test
```

## Configuration

Edit `~/.config/vibe-wellness/config.json`:

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

Remove the `vibe-wellness` hook entry from `~/.claude/settings.json`, then:

```bash
rm -rf ~/.vibe-wellness ~/.config/vibe-wellness
```

## Project structure

```
vibe_wellness/        # Python package
  config.py           # Config loading, i18n, language detection
  ui.py               # Overlay window (tkinter)
  config.json         # Default config + exercises
  gifs/               # Bundled exercise GIFs
scripts/
  show.sh             # Launch overlay (interval + single-instance guard)
  hide.sh             # Kill overlay
install.sh            # One-step installer
```
