# Whiplash

Slap your mouse, it yells back.

> "this is the most amazing thing i've ever seen" — [@kenwheeler](https://x.com/kenwheeler)

> "I just ran sexy mode with my wife sitting next to me...We died laughing" — [@duncanthedev](https://x.com/duncanthedev)

> "peak engineering" — [@tylertaewook](https://x.com/tylertaewook)

Windows port of [taigrr/spank](https://github.com/taigrr/spank). Uses `pynput` to detect physical acceleration spikes (jerk) on your mouse and plays audio responses. Pure Python script, lightweight and responsive.

## Requirements

- Windows 10/11
- Python 3.9+

## Install

Clone the repository and install the requirements:

```bash
git clone https://github.com/nexuspy/Whiplash.git
cd Whiplash
pip install -r requirements.txt
```

## Usage

```bash
# Normal mode — says "ow!" when you flick the mouse
python whiplash.py

# Sexy mode — escalating responses based on slap frequency
python whiplash.py --sexy

# Halo mode — plays Halo death sounds when slapped
python whiplash.py --halo

# Fast mode — faster detection threshold and shorter cooldown
python whiplash.py --fast
python whiplash.py --sexy --fast

# Custom mode — plays your own MP3/WAV/OGG files from a directory
python whiplash.py --custom C:\path\to\sounds

# Adjust sensitivity with jerk threshold (lower = more sensitive)
python whiplash.py --sensitivity 1.0   # more sensitive
python whiplash.py --sensitivity 3.0   # less sensitive
python whiplash.py --sexy --sensitivity 1.5

# Set cooldown period in milliseconds (default: 750)
python whiplash.py --cooldown 600
```

### Modes

**Pain mode** (default): Randomly plays from 10 pain/protest audio clips when a slap is detected.

**Sexy mode** (`--sexy`): Tracks slaps within a rolling 5-minute window. The more you slap, the more intense the audio response. 60 levels of escalation.

**Halo mode** (`--halo`): Randomly plays from death sound effects from the Halo video game series when a slap is detected.

**Custom mode** (`--custom`): Randomly plays audio files from a custom directory you specify.

### Detection tuning

Use `--fast` for a more responsive profile with a shorter cooldown (350ms vs 750ms) and higher baseline tracking sensitivity.

You can still override individual values with `--sensitivity` and `--cooldown` when needed.

### Sensitivity

Control detection sensitivity with `--sensitivity` (default: `2.0` px/ms²):

- Lower values (e.g., 0.8-1.2): Very sensitive, detects light quick flicks
- Medium values (e.g., 1.5-2.0): Balanced sensitivity, natural swipe
- Higher values (e.g., 2.5-4.0): Only strong, violent throws trigger sounds

The value represents the sudden spike in mouse acceleration (jerk) required to trigger a sound. The sensitivity is automatically scaled to your screen resolution internally so it feels identical across 1080p and 4K displays.

## Running in the Background at Startup

To have Whiplash start automatically hidden in the background when you boot your PC, you can add a simple script to your Windows Startup folder. Pick your mode:

<details>
<summary>Pain mode (default)</summary>

```powershell
# Run this in PowerShell to create a startup script
$shortcut = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\run_whiplash.bat"
"@echo off`nstart /B pythonw.exe ""$PWD\whiplash.py""" | Out-File -Encoding ASCII $shortcut
```

</details>

<details>
<summary>Sexy mode</summary>

```powershell
# Run this in PowerShell to create a startup script
$shortcut = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\run_whiplash.bat"
"@echo off`nstart /B pythonw.exe ""$PWD\whiplash.py"" --sexy" | Out-File -Encoding ASCII $shortcut
```

</details>

<details>
<summary>Halo mode</summary>

```powershell
# Run this in PowerShell to create a startup script
$shortcut = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\run_whiplash.bat"
"@echo off`nstart /B pythonw.exe ""$PWD\whiplash.py"" --halo" | Out-File -Encoding ASCII $shortcut
```

</details>

To stop it from running at system startup later, just delete the `run_whiplash.bat` file from your `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\` folder.

## How it works

1. `pynput` listens to global mouse movement events in the background.
2. Runs jerk detection calculations (Sudden Δvelocity / Δtime).
3. When a significant physical impact/flick is detected, plays an embedded audio response via `pygame`.
4. 750ms cooldown between responses to prevent rapid-fire, adjustable with `--cooldown`.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=nexuspy/Whiplash&type=date&legend=top-left)](https://www.star-history.com/#nexuspy/Whiplash&type=date&legend=top-left)

## Credits

Inspired by and audio assets ported directly from [taigrr/spank](https://github.com/taigrr/spank).
