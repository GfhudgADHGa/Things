#!/usr/bin/env python3
"""Generates a random point cloud, computes its convex hull and closest
pair, and renders a PNG showing all three. Pillow is used only for
drawing; the geometry itself (geometry/) has no dependencies."""
from __future__ import annotations

import argparse
import random

from PIL import Image, ImageDraw

from geometry import closest_pair, graham_scan


def render(points, hull, pair, width, height, margin=40):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    scale_x = (width - 2 * margin) / (max_x - min_x or 1)
    scale_y = (height - 2 * margin) / (max_y - min_y or 1)
    scale = min(scale_x, scale_y)

    def to_screen(p):
        x = margin + (p[0] - min_x) * scale
        y = height - margin - (p[1] - min_y) * scale  # flip: image y grows downward
        return (x, y)

    img = Image.new("RGB", (width, height), (18, 18, 24))
    draw = ImageDraw.Draw(img)

    # convex hull, filled translucent-looking outline
    if len(hull) >= 3:
        hull_screen = [to_screen(p) for p in hull]
        draw.polygon(hull_screen, outline=(90, 200, 250), fill=(40, 70, 90))

    # all points
    for p in points:
        x, y = to_screen(p)
        draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(220, 220, 230))

    # closest pair, highlighted
    (a, b) = pair
    ax, ay = to_screen(a)
    bx, by = to_screen(b)
    draw.line([ax, ay, bx, by], fill=(255, 90, 90), width=2)
    for x, y in [(ax, ay), (bx, by)]:
        draw.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(255, 90, 90), width=2)

    return img


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", type=int, default=60)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--width", type=int, default=600)
    parser.add_argument("--height", type=int, default=450)
    parser.add_argument("--output", default="geometry.png")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    points = [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(args.points)]

    hull = graham_scan(points)
    pair, dist = closest_pair(points)

    img = render(points, hull, pair, args.width, args.height)
    img.save(args.output)
    print(f"wrote {args.output}: {len(points)} points, hull has {len(hull)} vertices, "
          f"closest pair distance {dist:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
