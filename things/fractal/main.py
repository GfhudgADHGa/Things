#!/usr/bin/env python3
"""Render a Mandelbrot or Julia set to a PNG. Pillow is used only for
PNG encoding/writing here -- the fractal math itself (fractal/) has no
dependencies at all."""
from __future__ import annotations

import argparse

from PIL import Image

from fractal import render_julia, render_mandelbrot

JULIA_PRESETS = {
    "dendrite": -0.7 + 0.27015j,
    "rabbit": -0.123 + 0.745j,
    "spiral": -0.75 + 0.11j,
    "dust": -0.4 + 0.6j,
}


def _save(pixels, path: str) -> None:
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    img = Image.new("RGB", (width, height))
    img.putdata([px for row in pixels for px in row])
    img.save(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["mandelbrot", "julia"], default="mandelbrot")
    parser.add_argument("--julia-preset", choices=sorted(JULIA_PRESETS), default="dendrite")
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=600)
    parser.add_argument("--center-re", type=float, default=None)
    parser.add_argument("--center-im", type=float, default=None)
    parser.add_argument("--plane-width", type=float, default=3.0)
    parser.add_argument("--max-iter", type=int, default=500)
    parser.add_argument("--cycle", type=float, default=32.0)
    parser.add_argument("--output", default="fractal.png")
    args = parser.parse_args()

    if args.mode == "mandelbrot":
        center = complex(
            args.center_re if args.center_re is not None else -0.5,
            args.center_im if args.center_im is not None else 0.0,
        )
        pixels = render_mandelbrot(
            args.width, args.height, center=center, plane_width=args.plane_width,
            max_iter=args.max_iter, cycle=args.cycle,
        )
    else:
        c = JULIA_PRESETS[args.julia_preset]
        center = complex(
            args.center_re if args.center_re is not None else 0.0,
            args.center_im if args.center_im is not None else 0.0,
        )
        pixels = render_julia(
            c, args.width, args.height, center=center, plane_width=args.plane_width,
            max_iter=args.max_iter, cycle=args.cycle,
        )

    _save(pixels, args.output)
    print(f"wrote {args.output} ({args.width}x{args.height}, mode={args.mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
