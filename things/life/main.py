#!/usr/bin/env python3
"""Renders either a Game of Life run (as an animated GIF) or an
elementary 1D cellular automaton (as a static PNG, one row per
generation). Pillow is used only for image I/O here; the automata
themselves (life/) have no dependencies."""
from __future__ import annotations

import argparse
import random

from PIL import Image

from life.elementary import run as run_elementary
from life.elementary import single_seed_row
from life.grid import run as run_life
from life.patterns import GLIDER

CELL_SIZE = 8
BG = (15, 15, 20)
FG = (120, 220, 160)


def _random_soup(rng, width, height, density=0.35):
    return frozenset((x, y) for x in range(width) for y in range(height) if rng.random() < density)


def render_life_gif(cells, generations, width, height, output):
    frames = []
    history = run_life(cells, generations)
    for gen_cells in history:
        img = Image.new("RGB", (width * CELL_SIZE, height * CELL_SIZE), BG)
        pixels = img.load()
        for (x, y) in gen_cells:
            if 0 <= x < width and 0 <= y < height:
                for dx in range(CELL_SIZE):
                    for dy in range(CELL_SIZE):
                        pixels[x * CELL_SIZE + dx, y * CELL_SIZE + dy] = FG
        frames.append(img)
    frames[0].save(output, save_all=True, append_images=frames[1:], duration=120, loop=0)


def render_elementary_png(rule, width, generations, output):
    history = run_elementary(single_seed_row(width), rule=rule, generations=generations)
    img = Image.new("RGB", (width, len(history)), BG)
    pixels = img.load()
    for y, row in enumerate(history):
        for x, cell in enumerate(row):
            if cell:
                pixels[x, y] = FG
    img.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["life", "elementary"], default="life")
    parser.add_argument("--pattern", choices=["glider", "soup"], default="soup")
    parser.add_argument("--rule", type=int, default=90, help="elementary CA rule number, 0-255")
    parser.add_argument("--width", type=int, default=40)
    parser.add_argument("--height", type=int, default=30)
    parser.add_argument("--generations", type=int, default=60)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.mode == "life":
        output = args.output or "life.gif"
        if args.pattern == "glider":
            cells = frozenset((x + 2, y + 2) for x, y in GLIDER)
        else:
            rng = random.Random(args.seed)
            cells = _random_soup(rng, args.width, args.height)
        render_life_gif(cells, args.generations, args.width, args.height, output)
        print(f"wrote {output}: {args.generations} generations, {args.width}x{args.height} cells")
    else:
        output = args.output or f"rule{args.rule}.png"
        render_elementary_png(args.rule, args.width * 2, args.generations, output)
        print(f"wrote {output}: rule {args.rule}, {args.generations} generations")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
