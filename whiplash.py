#!/usr/bin/env python3
"""
whiplash.py — Core engine for Whiplash (Windows port of taigrr/spank)
Detects fast mouse flicks (≥ threshold) and plays sound effects.
"""

from __future__ import annotations
import argparse
import ctypes
import logging
import math
import os
import random
import struct
import sys
import threading
import time
import wave
import io
from collections import deque
from pathlib import Path
from typing import Callable, List, Optional

try:
    import pygame
except ImportError:
    print("[whiplash] pip install pygame")
    sys.exit(1)

try:
    from pynput import mouse
except ImportError:
    print("[whiplash] pip install pynput")
    sys.exit(1)

SOUNDS_DIR = Path(__file__).parent / "sounds"

log = logging.getLogger("whiplash")


def setup_logging(verbose: bool = False):
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    log.addHandler(ch)


def get_screen_width() -> int:
    try:
        return ctypes.windll.user32.GetSystemMetrics(0)
    except Exception:
        return 1920


def normalized_threshold(raw: float) -> float:
    return raw * (get_screen_width() / 1920.0)


SAMPLE_RATE = 22050
_SYNTH_PARAMS = [
    (800, 200, 180),
    (950, 250, 220),
    (700, 150, 160),
    (1100, 300, 250),
    (650, 100, 200),
    (900, 200, 190),
    (1050, 350, 270),
    (750, 180, 150),
    (850, 220, 210),
    (1000, 280, 230),
]


def _gen_wav(freq_s: int, freq_e: int, dur_ms: int, vol: float = 0.6) -> bytes:
    n = int(SAMPLE_RATE * dur_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        frames = []
        for i in range(n):
            t = i / SAMPLE_RATE
            frac = i / n
            freq = freq_s + (freq_e - freq_s) * frac
            env = math.exp(-frac * 6) * min(1.0, frac * 30)
            s = int(32767 * vol * env * math.sin(2 * math.pi * freq * t))
            s = max(-32768, min(32767, s))
            frames.append(struct.pack("<h", s))
        w.writeframes(b"".join(frames))
    return buf.getvalue()


def _build_synth_sounds() -> List[pygame.mixer.Sound]:
    log.info("Generating synthetic fallback sounds...")
    return [pygame.mixer.Sound(buffer=_gen_wav(*p)) for p in _SYNTH_PARAMS]


def _load_dir(path: Path, sorted_order: bool = False) -> List[pygame.mixer.Sound]:
    exts = (".mp3", ".wav", ".ogg")
    files = [f for f in path.iterdir() if f.suffix.lower() in exts]
    if sorted_order:
        files.sort(key=lambda f: f.name)
    sounds = []
    for f in files:
        try:
            sounds.append(pygame.mixer.Sound(str(f)))
        except Exception as e:
            log.warning(f"Could not load {f.name}: {e}")
    return sounds


def load_sounds(mode: str, custom_path: str = "") -> List[pygame.mixer.Sound]:
    if custom_path:
        p = Path(custom_path)
        if p.is_dir():
            sounds = _load_dir(p)
            if sounds:
                return sounds

    subdir = {"pain": "pain", "halo": "halo", "sexy": "sexy"}.get(mode, "pain")
    sound_dir = SOUNDS_DIR / subdir

    if sound_dir.is_dir():
        sounds = _load_dir(sound_dir, sorted_order=(mode == "sexy"))
        if sounds:
            return sounds

    return _build_synth_sounds()


class ShuffleDeck:
    def __init__(self, sounds: List[pygame.mixer.Sound]):
        self._sounds = sounds
        self._deck: List[pygame.mixer.Sound] = []
        self._last: Optional[pygame.mixer.Sound] = None
        self._lock = threading.Lock()

    def _refill(self):
        deck = list(self._sounds)
        random.shuffle(deck)
        if len(deck) > 1 and deck[0] is self._last:
            deck[0], deck[1] = deck[1], deck[0]
        self._deck = deck

    def play(self) -> Optional[pygame.mixer.Sound]:
        with self._lock:
            if not self._sounds:
                return None
            if not self._deck:
                self._refill()
            sound = self._deck.pop(0)
            self._last = sound
        sound.play()
        return sound


class SexyEscalator:
    WINDOW_S = 300

    def __init__(self, sounds: List[pygame.mixer.Sound]):
        self.sounds = sounds
        self.timestamps: deque = deque()
        self._lock = threading.Lock()

    def play(self) -> int:
        now = time.time()
        cutoff = now - self.WINDOW_S
        with self._lock:
            while self.timestamps and self.timestamps[0] < cutoff:
                self.timestamps.popleft()
            self.timestamps.append(now)
            count = len(self.timestamps)
            level = min(count - 1, len(self.sounds) - 1)
            if self.sounds:
                self.sounds[level].play()
        return level + 1


class MouseTracker:
    BUFFER = 6

    def __init__(self, threshold: float, cooldown_ms: int, on_slap: Callable):
        self.threshold = threshold
        self.cooldown_s = cooldown_ms / 1000.0
        self.on_slap = on_slap
        self._lock = threading.Lock()
        self._speeds: deque = deque(maxlen=self.BUFFER)
        self._times: deque = deque(maxlen=self.BUFFER)
        self._last_pos = None
        self._last_time = None
        self._last_trigger = 0.0

    def on_move(self, x: int, y: int):
        now = time.monotonic()
        with self._lock:
            if self._last_pos is not None:
                dx = x - self._last_pos[0]
                dy = y - self._last_pos[1]
                dt_s = now - self._last_time
                if dt_s > 0:
                    dt_ms = dt_s * 1000
                    speed = math.sqrt(dx * dx + dy * dy) / dt_ms
                    if self._speeds:
                        prev_speed = self._speeds[-1]
                        jerk = abs(speed - prev_speed) / dt_ms
                        since_last = now - self._last_trigger
                        if jerk >= self.threshold and since_last >= self.cooldown_s:
                            self._last_trigger = now
                            threading.Thread(
                                target=self.on_slap, args=(jerk,), daemon=True
                            ).start()
                    self._speeds.append(speed)
                    self._times.append(now)
            self._last_pos = (x, y)
            self._last_time = now


class WhiplashEngine:
    def __init__(self, mode: str, sensitivity: float, cooldown_ms: int, custom: str):
        pygame.mixer.pre_init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        self.slap_count = 0
        self._mode = mode
        sounds = load_sounds(mode, custom)
        self._deck = ShuffleDeck(sounds)
        self._escalator = SexyEscalator(sounds) if mode == "sexy" else None
        threshold = normalized_threshold(sensitivity)
        self._tracker = MouseTracker(threshold, cooldown_ms, self._on_slap)
        self._listener: Optional[mouse.Listener] = None

    def _on_slap(self, jerk: float):
        self.slap_count += 1
        if self._mode == "sexy" and self._escalator:
            level = self._escalator.play()
            log.info(f"💥 SLAP #{self.slap_count}  jerk={jerk:.2f}  level={level}/60")
        else:
            self._deck.play()
            log.info(f"💥 SLAP #{self.slap_count}  jerk={jerk:.2f}")

    def start(self):
        self._listener = mouse.Listener(on_move=self._tracker.on_move)
        self._listener.start()
        log.info(
            f"Started | mode={self._mode} | threshold={self._tracker.threshold:.2f} | cooldown={int(self._tracker.cooldown_s * 1000)}ms"
        )

    def stop(self):
        if self._listener:
            self._listener.stop()
        pygame.mixer.quit()


BANNER = r"""
 __    __ _     _       _           _
/ / /\ \ \ |__ (_)_ __ | | __ _ ___| |__
\ \/  \/ / '_ \| | '_ \| |/ _` / __| '_ \
 \  /\  /| | | | | |_) | | (_| \__ \ | | |
  \/  \/ |_| |_|_| .__/|_|\__,_|___/_| |_|
                 |_|
  Whiplash v2.0 — slap your mouse, it yells back.
"""


def main():
    setup_logging()
    p = argparse.ArgumentParser(description="Whiplash — mouse-flick sound player")
    p.add_argument("--sexy", action="store_true", help="Escalating sounds mode")
    p.add_argument("--halo", action="store_true", help="Halo death sounds mode")
    p.add_argument("--custom", metavar="PATH", default="", help="Custom sounds folder")
    p.add_argument(
        "--fast", action="store_true", help="High sensitivity + low cooldown toggle"
    )
    p.add_argument(
        "--sensitivity",
        type=float,
        default=2.0,
        help="Jerk threshold (lower is more sensitive, default 2.0)",
    )
    p.add_argument(
        "--cooldown", type=int, default=750, help="Minimum ms between sounds"
    )
    args = p.parse_args()

    mode = "pain"
    if args.sexy:
        mode = "sexy"
    elif args.halo:
        mode = "halo"
    elif args.custom:
        mode = "custom"

    sens = args.sensitivity * 0.6 if args.fast else args.sensitivity
    cd = 350 if args.fast else args.cooldown

    print(BANNER)
    print("Press Ctrl+C to quit.\n")
    engine = WhiplashEngine(mode, sens, cd, args.custom)
    engine.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print(f"\n[whiplash] Stopped. Total slaps: {engine.slap_count}")
    finally:
        engine.stop()


if __name__ == "__main__":
    main()
