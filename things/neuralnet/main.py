#!/usr/bin/env python3
"""Trains a small network on a 2D classification task and renders its
learned decision boundary to a PNG.
"""
from __future__ import annotations

import argparse
import math
import random

from neuralnet.activations import SIGMOID, TANH
from neuralnet.layer import Dense
from neuralnet.losses import MSE
from neuralnet.network import Sequential

TASKS = {}


def _circle_dataset(n: int, rng: random.Random):
    data = []
    for _ in range(n):
        x, y = rng.uniform(-1, 1), rng.uniform(-1, 1)
        label = 1.0 if (x * x + y * y) < 0.5 else 0.0
        data.append(([x, y], [label]))
    return data


def _xor_blobs_dataset(n: int, rng: random.Random):
    data = []
    for _ in range(n):
        x, y = rng.uniform(-1, 1), rng.uniform(-1, 1)
        label = 1.0 if (x > 0) != (y > 0) else 0.0
        data.append(([x, y], [label]))
    return data


def _spiral_dataset(n: int, rng: random.Random):
    data = []
    for i in range(n):
        cls = i % 2
        t = rng.uniform(0, 1) * 3.0
        angle = t * 2.5 * math.pi + cls * math.pi
        radius = t / 3.0
        x = radius * math.cos(angle) + rng.uniform(-0.03, 0.03)
        y = radius * math.sin(angle) + rng.uniform(-0.03, 0.03)
        data.append(([x, y], [float(cls)]))
    return data


TASKS = {"circle": _circle_dataset, "xor_blobs": _xor_blobs_dataset, "spiral": _spiral_dataset}


def render_boundary(net: Sequential, dataset, path: str, resolution: int = 200) -> None:
    from PIL import Image

    img = Image.new("RGB", (resolution, resolution))
    pixels = img.load()

    for py in range(resolution):
        y = 1.0 - 2.0 * py / (resolution - 1)
        for px in range(resolution):
            x = -1.0 + 2.0 * px / (resolution - 1)
            pred = net.forward([x, y])[0]
            # background: soft blue -> soft red as confidence shifts
            t = max(0.0, min(1.0, pred))
            r = int(60 + t * 180)
            b = int(240 - t * 180)
            pixels[px, py] = (r, 90, b)

    for (x, y), (label,) in dataset:
        px = int((x + 1.0) / 2.0 * (resolution - 1))
        py = int((1.0 - y) / 2.0 * (resolution - 1))
        color = (255, 230, 60) if label > 0.5 else (20, 20, 20)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                nx, ny = px + dx, py + dy
                if 0 <= nx < resolution and 0 <= ny < resolution:
                    pixels[nx, ny] = color

    img.save(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=sorted(TASKS), default="circle")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=400)
    parser.add_argument("--learning-rate", type=float, default=0.3)
    parser.add_argument("--output", default="boundary.png")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    dataset = TASKS[args.task](300, rng)
    net = Sequential([
        Dense(2, 16, TANH, rng),
        Dense(16, 12, TANH, rng),
        Dense(12, 1, SIGMOID, rng),
    ])

    for epoch in range(args.epochs):
        loss = net.train_epoch(dataset, MSE, args.learning_rate)
        if epoch % max(1, args.epochs // 5) == 0:
            print(f"epoch {epoch}: loss={loss:.4f}")

    correct = sum(1 for x, y in dataset if round(net.forward(x)[0]) == y[0])
    print(f"final training accuracy: {correct}/{len(dataset)}")

    render_boundary(net, dataset, args.output)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
