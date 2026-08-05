#!/usr/bin/env python3
"""Demonstrates all three probabilistic data structures on synthetic
data and renders a chart of HyperLogLog's estimated vs. true
cardinality as the true count grows across several orders of magnitude.
Pillow is used only for drawing; probds/ itself has zero dependencies.
"""
from __future__ import annotations

import argparse
import math
import random

from PIL import Image, ImageDraw

from probds import BloomFilter, CountMinSketch, HyperLogLog

BG = (15, 15, 20)
AXIS_COLOR = (90, 95, 110)
IDEAL_COLOR = (70, 75, 90)
ESTIMATE_COLOR = (120, 220, 160)
TEXT_COLOR = (220, 225, 235)


def demo_bloom_filter(seed=0):
    rng = random.Random(seed)
    n = 5000
    bf = BloomFilter(expected_items=n, false_positive_rate=0.01)
    members = [f"user-{i}@example.com" for i in range(n)]
    for m in members:
        bf.add(m)
    false_positives = sum(1 for i in range(20000) if f"absent-{i}@example.com" in bf)
    print(f"[bloom]   {n} items, target fpr=1%, predicted fpr={bf.predicted_false_positive_rate():.4f}, "
          f"measured over 20000 non-members: {false_positives / 20000:.4f}")


def demo_count_min_sketch(seed=0):
    rng = random.Random(seed)
    cms = CountMinSketch.for_error_bound(epsilon=0.001, delta=0.01)
    words = ["the", "quick", "brown", "fox", "jumps", "over", "a", "lazy", "dog"]
    weights = [50, 10, 8, 6, 5, 5, 40, 4, 7]
    stream = rng.choices(words, weights=weights, k=200000)
    for w in stream:
        cms.add(w)
    from collections import Counter
    truth = Counter(stream)
    print(f"[cms]     {cms.width}x{cms.depth} sketch over {cms.total} events, {len(words)} distinct words:")
    for w in words:
        print(f"          {w!r:10s} true={truth[w]:6d}  estimate={cms.estimate(w):6d}")


def render_hll_chart(width, height, output, seed=0):
    rng = random.Random(seed)
    b = 12
    points = []
    exponents = [i * 0.15 for i in range(1, 34)]
    for e in exponents:
        n = max(1, round(10 ** e))
        hll = HyperLogLog(b=b)
        for i in range(n):
            hll.add(f"item-{seed}-{i}")
        points.append((n, hll.estimate()))

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    margin = 60
    max_val = max(p[0] for p in points) * 1.1
    min_val = 1

    def to_px(n):
        # log-log axes
        log_frac = (math.log10(max(n, 1)) - math.log10(min_val)) / (math.log10(max_val) - math.log10(min_val))
        return margin + log_frac * (width - 2 * margin)

    draw.line([(margin, height - margin), (width - margin, height - margin)], fill=AXIS_COLOR, width=2)
    draw.line([(margin, margin), (margin, height - margin)], fill=AXIS_COLOR, width=2)

    # ideal estimate == true line
    ideal_points = [(to_px(n), height - margin - (to_px(n) - margin)) for n, _ in points]
    draw.line(ideal_points, fill=IDEAL_COLOR, width=2)

    for n, est in points:
        x = to_px(n)
        y = height - margin - (to_px(est) - margin)
        r = 4
        draw.ellipse([x - r, y - r, x + r, y + r], fill=ESTIMATE_COLOR)

    draw.text((margin, height - margin + 15), "true cardinality (log scale) -->", fill=TEXT_COLOR)
    draw.text((10, margin - 15), "estimate", fill=TEXT_COLOR)
    draw.text((margin, 15), f"HyperLogLog (b={b}, m={1 << b} registers) estimate vs. true cardinality", fill=TEXT_COLOR)
    img.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default="hll_convergence.png")
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=600)
    args = parser.parse_args()

    demo_bloom_filter(args.seed)
    demo_count_min_sketch(args.seed)
    render_hll_chart(args.width, args.height, args.output, seed=args.seed)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
