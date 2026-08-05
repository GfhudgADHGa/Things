#!/usr/bin/env python3
"""Demonstrates the four rate limiters on the same "saved-up-budget"
scenario -- rate requests right before a window boundary, rate more
right after -- and renders a chart of how many each one lets through
in that tight span. Pillow is used only for drawing; ratelimit/ itself
has zero dependencies.
"""
from __future__ import annotations

import argparse

from PIL import Image, ImageDraw

from ratelimit import FixedWindowCounter, SlidingWindowCounter, SlidingWindowLog, TokenBucket

BG = (15, 15, 20)
BAR_COLOR = (120, 220, 160)
BAR_BAD = (200, 110, 100)
AXIS_COLOR = (90, 95, 110)
TEXT_COLOR = (220, 225, 235)

RATE = 10
WINDOW = 10.0


def boundary_burst_counts():
    results = {}

    fixed = FixedWindowCounter(rate=RATE, window_size=WINDOW)
    results["fixed window"] = sum(fixed.allow(9.99) for _ in range(RATE)) + sum(
        fixed.allow(10.01) for _ in range(RATE)
    )

    log = SlidingWindowLog(rate=RATE, window_size=WINDOW)
    results["sliding log"] = sum(log.allow(9.99) for _ in range(RATE)) + sum(
        log.allow(10.01) for _ in range(RATE)
    )

    counter = SlidingWindowCounter(rate=RATE, window_size=WINDOW)
    results["sliding counter"] = sum(counter.allow(9.99) for _ in range(RATE)) + sum(
        counter.allow(10.01) for _ in range(RATE)
    )

    # token bucket doesn't have a "window" concept at all, so there's no
    # analogous boundary to straddle -- included for scale, using the
    # equivalent rate/capacity and the same 0.02s span
    bucket = TokenBucket(rate=RATE / WINDOW, capacity=RATE)
    results["token bucket"] = sum(bucket.allow(9.99) for _ in range(RATE)) + sum(
        bucket.allow(10.01) for _ in range(RATE)
    )

    return results


def render_chart(width, height, output):
    counts = boundary_burst_counts()
    print(f"[ratelimit] rate={RATE}, window={WINDOW}s -- requests allowed in a 0.02s span straddling a boundary:")
    for name, count in counts.items():
        print(f"  {name:18s} {count:3d}  (configured rate: {RATE})")

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    margin = 70
    max_val = max(counts.values()) * 1.2
    names = list(counts.keys())
    bar_w = (width - 2 * margin) / len(names) * 0.5
    gap = (width - 2 * margin) / len(names)

    draw.text((margin, 20), f"requests allowed within 0.02s of a window boundary (configured rate = {RATE})", fill=TEXT_COLOR)
    draw.line([(margin, height - margin), (width - margin, height - margin)], fill=AXIS_COLOR, width=2)

    rate_y = height - margin - (RATE / max_val) * (height - 2 * margin)
    draw.line([(margin, rate_y), (width - margin, rate_y)], fill=AXIS_COLOR, width=1)
    draw.text((width - margin - 90, rate_y - 16), "configured rate", fill=TEXT_COLOR)

    for i, name in enumerate(names):
        count = counts[name]
        x0 = margin + i * gap + (gap - bar_w) / 2
        bar_h = (count / max_val) * (height - 2 * margin)
        y1 = height - margin
        y0 = y1 - bar_h
        color = BAR_BAD if count > RATE * 1.3 else BAR_COLOR
        draw.rectangle([x0, y0, x0 + bar_w, y1], fill=color)
        draw.text((x0, y0 - 16), str(count), fill=TEXT_COLOR)
        draw.text((x0 - 10, y1 + 10), name, fill=TEXT_COLOR)

    img.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="boundary_burst.png")
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=600)
    args = parser.parse_args()

    render_chart(args.width, args.height, args.output)
    print(f"\nwrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
