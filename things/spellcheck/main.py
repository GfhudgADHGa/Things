#!/usr/bin/env python3
"""Demos the spell checker on a handful of classic typos, and renders a
bar chart comparing how many edit-distance computations a BK-tree query
needs versus a brute-force scan of the whole dictionary -- the actual
payoff of the triangle-inequality pruning described in bk_tree.py.
Pillow is used only for drawing; spellcheck/ itself has zero
dependencies.
"""
from __future__ import annotations

import argparse

from PIL import Image, ImageDraw

from spellcheck import BKTree, SpellChecker, COMMON_WORDS, levenshtein

BG = (15, 15, 20)
BAR_BRUTE = (200, 110, 100)
BAR_BKTREE = (120, 220, 160)
AXIS_COLOR = (90, 95, 110)
TEXT_COLOR = (220, 225, 235)

TYPOS = ["recieve", "wich", "beleive", "langauge", "thier", "goverment", "freind", "existance"]


def demo_suggestions():
    checker = SpellChecker(COMMON_WORDS)
    print(f"[spellcheck] dictionary: {len(COMMON_WORDS)} words\n")
    for typo in TYPOS:
        suggestions = checker.suggest(typo, max_dist=2)[:5]
        rendered = ", ".join(f"{w} ({d})" for w, d in suggestions) or "(no suggestions within distance 2)"
        print(f"  {typo:12s} -> {rendered}")


def _counting_distance_fn():
    calls = [0]

    def fn(a, b):
        calls[0] += 1
        return levenshtein(a, b)

    return fn, calls


def measure_comparisons(max_dists):
    bktree_counts = []
    brute_counts = []
    for max_dist in max_dists:
        fn, calls = _counting_distance_fn()
        tree = BKTree(fn)
        for w in COMMON_WORDS:
            tree.insert(w)
        calls[0] = 0  # only count query-time comparisons, not build time
        tree.query("langauge", max_dist)
        bktree_counts.append(calls[0])
        brute_counts.append(len(COMMON_WORDS))
    return bktree_counts, brute_counts


def render_comparison_chart(width, height, output):
    max_dists = [1, 2, 3, 4]
    bktree_counts, brute_counts = measure_comparisons(max_dists)

    print("\n[pruning] edit-distance computations for a fuzzy query, by max_dist:")
    for d, bk, brute in zip(max_dists, bktree_counts, brute_counts):
        print(f"  max_dist={d}:  BK-tree={bk:5d}   brute-force={brute:5d}   ({brute / max(bk, 1):.1f}x fewer)")

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    margin = 70
    max_val = max(brute_counts) * 1.15
    group_w = (width - 2 * margin) / len(max_dists)

    draw.line([(margin, height - margin), (width - margin, height - margin)], fill=AXIS_COLOR, width=2)
    draw.text((margin, 20), "edit-distance computations per fuzzy query (lower is better)", fill=TEXT_COLOR)

    for i, d in enumerate(max_dists):
        gx = margin + i * group_w
        bar_w = group_w * 0.32
        for j, (val, color) in enumerate([(brute_counts[i], BAR_BRUTE), (bktree_counts[i], BAR_BKTREE)]):
            x0 = gx + group_w * 0.15 + j * (bar_w + 6)
            bar_h = (val / max_val) * (height - 2 * margin)
            y1 = height - margin
            y0 = y1 - bar_h
            draw.rectangle([x0, y0, x0 + bar_w, y1], fill=color)
            draw.text((x0, y0 - 16), str(val), fill=TEXT_COLOR)
        draw.text((gx + group_w * 0.3, height - margin + 12), f"max_dist={d}", fill=TEXT_COLOR)

    draw.rectangle([width - 220, 20, width - 205, 35], fill=BAR_BRUTE)
    draw.text((width - 195, 20), "brute-force (whole dictionary)", fill=TEXT_COLOR)
    draw.rectangle([width - 220, 40, width - 205, 55], fill=BAR_BKTREE)
    draw.text((width - 195, 40), "BK-tree", fill=TEXT_COLOR)

    img.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="pruning_comparison.png")
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=600)
    args = parser.parse_args()

    demo_suggestions()
    render_comparison_chart(args.width, args.height, args.output)
    print(f"\nwrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
