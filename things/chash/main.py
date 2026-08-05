#!/usr/bin/env python3
"""Demonstrates the two headline properties of consistent hashing --
minimal disruption on node changes, and load uniformity from virtual
nodes -- and renders a bar chart comparing key-load distribution across
nodes with few vs. many virtual nodes per physical node. Pillow is used
only for drawing; chash/ itself has zero dependencies."""
from __future__ import annotations

import argparse
import random
import statistics

from PIL import Image, ImageDraw

from chash.naive import naive_route
from chash.ring import ConsistentHashRing

BG = (15, 15, 20)
BAR_FEW = (200, 110, 100)
BAR_MANY = (120, 220, 160)
AXIS_COLOR = (90, 95, 110)
TEXT_COLOR = (220, 225, 235)


def demo_minimal_disruption(seed=0):
    rng = random.Random(seed)
    n_nodes = 10
    keys = [f"key-{i}" for i in range(20000)]
    nodes = [f"node-{i}" for i in range(n_nodes)]

    ring = ConsistentHashRing(virtual_nodes_per_physical=200)
    for n in nodes:
        ring.add_node(n)
    before = {k: ring.get_node(k) for k in keys}
    ring.add_node("new-node")
    after = {k: ring.get_node(k) for k in keys}
    ch_fraction = sum(1 for k in keys if before[k] != after[k]) / len(keys)

    naive_before = {k: naive_route(k, nodes) for k in keys}
    naive_after = {k: naive_route(k, nodes + ["new-node"]) for k in keys}
    naive_fraction = sum(1 for k in keys if naive_before[k] != naive_after[k]) / len(keys)

    print(f"[disruption]  {n_nodes} -> {n_nodes + 1} nodes, {len(keys)} keys")
    print(f"              consistent hashing remapped {ch_fraction:.1%}  (theoretical ~{1 / (n_nodes + 1):.1%})")
    print(f"              naive mod-n hashing remapped {naive_fraction:.1%}")


def render_load_chart(width, height, output, seed=0):
    rng = random.Random(seed)
    n_nodes = 8
    keys = [f"key-{i}" for i in range(20000)]
    nodes = [f"node-{i}" for i in range(n_nodes)]

    def loads(vnodes):
        ring = ConsistentHashRing(virtual_nodes_per_physical=vnodes)
        for n in nodes:
            ring.add_node(n)
        counts = {n: 0 for n in nodes}
        for k in keys:
            counts[ring.get_node(k)] += 1
        return [counts[n] for n in nodes]

    loads_few = loads(1)
    loads_many = loads(200)
    cv_few = statistics.stdev(loads_few) / statistics.mean(loads_few)
    cv_many = statistics.stdev(loads_many) / statistics.mean(loads_many)
    print(f"[uniformity]  1 vnode/node:   coefficient of variation = {cv_few:.3f}")
    print(f"              200 vnodes/node: coefficient of variation = {cv_many:.3f}")

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    margin = 60
    chart_h = (height - 3 * margin) // 2
    max_load = max(max(loads_few), max(loads_many)) * 1.15

    def draw_bars(loads_vals, top, color, label):
        draw.text((margin, top - 20), label, fill=TEXT_COLOR)
        bar_w = (width - 2 * margin) / len(loads_vals) * 0.7
        gap = (width - 2 * margin) / len(loads_vals)
        for i, load in enumerate(loads_vals):
            x0 = margin + i * gap + (gap - bar_w) / 2
            bar_h = (load / max_load) * chart_h
            y1 = top + chart_h
            y0 = y1 - bar_h
            draw.rectangle([x0, y0, x0 + bar_w, y1], fill=color)
        draw.line([(margin, top + chart_h), (width - margin, top + chart_h)], fill=AXIS_COLOR, width=2)

    draw_bars(loads_few, margin, BAR_FEW, "1 virtual node per physical node (uneven)")
    draw_bars(loads_many, margin + chart_h + margin, BAR_MANY, "200 virtual nodes per physical node (even)")

    img.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default="load_distribution.png")
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=600)
    args = parser.parse_args()

    demo_minimal_disruption(args.seed)
    render_load_chart(args.width, args.height, args.output, seed=args.seed)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
