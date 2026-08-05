"""Rasterizes a World's circles into a grid of RGB pixels."""
from __future__ import annotations

from typing import List, Tuple

from .world import World

Color = Tuple[int, int, int]


def render_frame(world: World, width: int, height: int, background: Color = (245, 245, 245)) -> List[List[Color]]:
    frame = [[background for _ in range(width)] for _ in range(height)]

    for body in world.bodies:
        cx, cy, r = body.position.x, body.position.y, body.radius
        x0, x1 = max(0, int(cx - r)), min(width - 1, int(cx + r))
        y0, y1 = max(0, int(cy - r)), min(height - 1, int(cy + r))
        r_sq = r * r
        for y in range(y0, y1 + 1):
            dy = y + 0.5 - cy
            for x in range(x0, x1 + 1):
                dx = x + 0.5 - cx
                if dx * dx + dy * dy <= r_sq:
                    frame[y][x] = body.color

    return frame
