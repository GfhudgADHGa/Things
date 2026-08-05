#!/usr/bin/env python3
"""CLI entry point: render one of the example scenes to a PNG."""
from __future__ import annotations

import argparse
import sys
import time

from raytracer.png_writer import write_png
from raytracer.render import render
from raytracer.scenes import SCENES


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", choices=sorted(SCENES), default="three_spheres")
    parser.add_argument("--width", type=int, default=400)
    parser.add_argument("--height", type=int, default=None, help="defaults to width / aspect ratio")
    parser.add_argument("--samples", type=int, default=50, help="samples per pixel")
    parser.add_argument("--depth", type=int, default=10, help="max ray bounce depth")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=None, help="parallel worker processes")
    parser.add_argument("--output", default="render.png")
    args = parser.parse_args(argv)

    scene_fn = SCENES[args.scene]
    aspect_ratio = 16 / 9 if args.scene != "random_field" else 3 / 2
    world, camera = scene_fn(aspect_ratio=aspect_ratio)

    height = args.height or int(args.width / aspect_ratio)

    start = time.time()
    rows = render(
        world,
        camera,
        image_width=args.width,
        image_height=height,
        samples_per_pixel=args.samples,
        max_depth=args.depth,
        seed=args.seed,
        workers=args.workers,
    )
    elapsed = time.time() - start

    write_png(rows, args.output)
    print(
        f"Rendered '{args.scene}' at {args.width}x{height}, "
        f"{args.samples} spp, depth {args.depth} -> {args.output} in {elapsed:.1f}s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
