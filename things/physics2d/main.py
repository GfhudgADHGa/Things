#!/usr/bin/env python3
"""Simulate bouncing balls and render the result as an animated GIF."""
from __future__ import annotations

import argparse
import random

from physics2d import Circle, Vec2, World, encode_gif, render_frame

COLORS = [
    (220, 60, 60), (60, 140, 220), (60, 200, 100),
    (230, 180, 50), (180, 80, 220), (60, 200, 200),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=200)
    parser.add_argument("--height", type=int, default=150)
    parser.add_argument("--balls", type=int, default=8)
    parser.add_argument("--frames", type=int, default=90)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default="bounce.gif")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    world = World(width=args.width, height=args.height)
    for i in range(args.balls):
        world.add(Circle(
            position=Vec2(rng.uniform(20, args.width - 20), rng.uniform(10, args.height / 2)),
            velocity=Vec2(rng.uniform(-80, 80), 0),
            radius=rng.uniform(6, 14),
            mass=1.0,
            restitution=rng.uniform(0.6, 0.9),
            color=COLORS[i % len(COLORS)],
        ))

    dt = 1.0 / args.fps
    steps_per_frame = 2
    frames = []
    for _ in range(args.frames):
        for _ in range(steps_per_frame):
            world.step(dt / steps_per_frame)
        frames.append(render_frame(world, args.width, args.height))

    encode_gif(frames, args.output, delay_ms=int(1000 / args.fps))
    print(f"Wrote {args.output}: {args.frames} frames, {args.balls} balls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
