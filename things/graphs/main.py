#!/usr/bin/env python3
"""Generates a random weighted graph, runs the MST and shortest-path
algorithms on it, and renders it to a PNG via a small hand-rolled
force-directed layout (Fruchterman-Reingold style: nodes repel each
other, edges pull their endpoints together, positions relax over many
iterations). Pillow is used only for drawing; graphs/ itself has zero
dependencies."""
from __future__ import annotations

import argparse
import math
import random

from PIL import Image, ImageDraw

from graphs.graph import Graph
from graphs.mst import kruskal, total_weight
from graphs.shortest_path import dijkstra

BG = (15, 15, 20)
NODE_FILL = (40, 45, 60)
NODE_OUTLINE = (150, 170, 220)
EDGE_COLOR = (60, 65, 80)
MST_COLOR = (120, 220, 160)
TEXT_COLOR = (220, 225, 235)


def _random_graph(rng, n, edge_prob, weight_range):
    g = Graph(directed=False)
    nodes = list(range(n))
    rng.shuffle(nodes)
    for i in range(1, n):
        u = nodes[i]
        v = nodes[rng.randint(0, i - 1)]
        g.add_edge(u, v, round(rng.uniform(*weight_range), 1))
    for u in range(n):
        for v in range(u + 1, n):
            if rng.random() < edge_prob:
                g.add_edge(u, v, round(rng.uniform(*weight_range), 1))
    return g


def _force_directed_layout(g, width, height, iterations=400, seed=0):
    rng = random.Random(seed)
    nodes = g.nodes()
    pos = {u: (rng.uniform(0.1, 0.9) * width, rng.uniform(0.1, 0.9) * height) for u in nodes}
    area = width * height
    k = math.sqrt(area / max(len(nodes), 1))

    for it in range(iterations):
        disp = {u: [0.0, 0.0] for u in nodes}
        for u in nodes:
            for v in nodes:
                if u == v:
                    continue
                dx = pos[u][0] - pos[v][0]
                dy = pos[u][1] - pos[v][1]
                dist = max(math.hypot(dx, dy), 0.01)
                force = k * k / dist
                disp[u][0] += dx / dist * force
                disp[u][1] += dy / dist * force
        for u, v, _ in g.edges():
            dx = pos[u][0] - pos[v][0]
            dy = pos[u][1] - pos[v][1]
            dist = max(math.hypot(dx, dy), 0.01)
            force = dist * dist / k
            disp[u][0] -= dx / dist * force
            disp[u][1] -= dy / dist * force
            disp[v][0] += dx / dist * force
            disp[v][1] += dy / dist * force

        temperature = width * 0.1 * (1 - it / iterations)
        for u in nodes:
            dx, dy = disp[u]
            dist = max(math.hypot(dx, dy), 0.01)
            step = min(dist, temperature)
            x = pos[u][0] + dx / dist * step
            y = pos[u][1] + dy / dist * step
            margin = 30
            x = min(max(x, margin), width - margin)
            y = min(max(y, margin), height - margin)
            pos[u] = (x, y)
    return pos


def render_graph_png(g, mst_edges, width, height, output, seed=0):
    pos = _force_directed_layout(g, width, height, seed=seed)
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    mst_set = {frozenset((u, v)) for u, v, _ in mst_edges}

    for u, v, w in g.edges():
        is_mst = frozenset((u, v)) in mst_set
        color = MST_COLOR if is_mst else EDGE_COLOR
        width_px = 3 if is_mst else 1
        draw.line([pos[u], pos[v]], fill=color, width=width_px)

    radius = 14
    for u in g.nodes():
        x, y = pos[u]
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=NODE_FILL, outline=NODE_OUTLINE, width=2)
        label = str(u)
        bbox = draw.textbbox((0, 0), label)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((x - tw / 2, y - th / 2 - 2), label, fill=TEXT_COLOR)

    img.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", type=int, default=14)
    parser.add_argument("--edge-prob", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=600)
    parser.add_argument("--output", default="graph.png")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    g = _random_graph(rng, args.nodes, args.edge_prob, (1.0, 20.0))
    mst_edges = kruskal(g)
    dist = dijkstra(g, 0)

    print(f"{args.nodes} nodes, {len(g.edges())} edges")
    print(f"MST total weight: {total_weight(mst_edges):.1f} ({len(mst_edges)} edges, highlighted in green)")
    reachable = sum(1 for d in dist.values() if d != float("inf"))
    print(f"shortest paths from node 0: {reachable}/{args.nodes} nodes reachable")

    render_graph_png(g, mst_edges, args.width, args.height, args.output, seed=args.seed)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
