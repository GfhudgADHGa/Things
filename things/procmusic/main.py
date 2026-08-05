#!/usr/bin/env python3
"""Generate a short piece of algorithmic music and save it as a .wav file."""
from __future__ import annotations

import argparse

from procmusic import compose, write_wav

PRESETS = {
    "calm": dict(key="C4", scale_name="major", progression=("I", "vi", "IV", "V"), tempo_bpm=80),
    "upbeat": dict(key="D4", scale_name="major", progression=("I", "V", "vi", "IV"), tempo_bpm=128),
    "melancholy": dict(key="A3", scale_name="natural_minor", progression=("I", "vi", "iii", "vii"), tempo_bpm=70),
    "bluesy": dict(key="E3", scale_name="blues", progression=("I", "IV", "I", "V"), tempo_bpm=95),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=sorted(PRESETS), default="calm")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--repeats", type=int, default=2, help="how many times to loop the progression")
    parser.add_argument("--no-drums", action="store_true", help="disable the drum track")
    parser.add_argument("--output", default="song.wav")
    args = parser.parse_args()

    settings = dict(PRESETS[args.preset])
    settings["progression"] = tuple(settings["progression"]) * args.repeats
    settings["seed"] = args.seed
    settings["drums"] = not args.no_drums

    samples = compose(**settings)
    write_wav(samples, args.output)
    drum_note = "" if args.no_drums else " + drums"
    print(f"Wrote {args.output}: {len(samples) / 44100:.1f}s, preset={args.preset!r}, seed={args.seed}{drum_note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
