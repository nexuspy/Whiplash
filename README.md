# Whiplash 🖱️💥

> _Slap your mouse, it yells back._  
> Windows port of [taigrr/spank](https://github.com/taigrr/spank).

Instead of an accelerometer (macOS-only), Whiplash detects **fast mouse flicks** — throw your mouse across the screen at 2× normal speed, and it screams "OW!".

---

## Requirements

- Python 3.10+
- Windows 10/11

## Usage

Open a terminal or command prompt in this folder:

```bash
# Install dependencies (one time)
pip install -r requirements.txt

# Run!
python whiplash.py
```

_When running, just flick/throw your mouse aggressively across the screen. It should trigger the pain sound immediately._

To stop the script, press `Ctrl+C` in the terminal.

### Advanced Flags

```bash
# Escalating sexy mode
python whiplash.py --sexy

# Halo death sounds
python whiplash.py --halo

# High sensitivity + 350ms cooldown
python whiplash.py --fast


# Set cooldown between triggers in milliseconds (default: 750)
python whiplash.py --cooldown 400

# Combine flags
python whiplash.py --sexy --fast --cooldown 300
```

## Sensitivity Guide

| Value | Feel                                           |
| ----- | ---------------------------------------------- |
| `0.8` | Very sensitive — light quick flicks trigger it |
| `1.5` | Balanced — natural fast swipe                  |
| `2.0` | Default — needs a proper aggressive flick      |
| `3.0` | Hard to trigger — only violent throws          |

## Adding Real Sounds

Drop your own `.wav`, `.mp3`, or `.ogg` files into:

```
sounds/
  pain/     ← used in default and --sexy mode
  halo/     ← used in --halo mode
```

If no files are found, Whiplash generates synthetic "yelp" tones automatically so it always works out of the box.

## How It Works

1. `pynput` listens to global mouse movement events (no admin rights needed)
2. Computes velocity `sqrt(dx² + dy²) / dt` in px/ms over a rolling 8-sample buffer
3. When peak velocity ≥ threshold **and** cooldown has elapsed → triggers a random sound via `pygame.mixer`
4. In `--sexy` mode, a 5-minute rolling slap counter maps to 60 escalation levels

## License

MIT
