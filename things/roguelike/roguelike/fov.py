"""Field of view: which tiles can the player currently see."""
from __future__ import annotations

from typing import List, Set

from .dungeon import WALL, Dungeon
from .geometry import Point


def bresenham_line(p0: Point, p1: Point) -> List[Point]:
    x0, y0 = p0.x, p0.y
    x1, y1 = p1.x, p1.y
    points = []

    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy

    x, y = x0, y0
    while True:
        points.append(Point(x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy

    return points


def compute_fov(dungeon: Dungeon, origin: Point, radius: int) -> Set[Point]:
    visible: Set[Point] = {origin}

    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy > radius * radius:
                continue
            target = Point(origin.x + dx, origin.y + dy)
            if not dungeon.is_in_bounds(target):
                continue

            for point in bresenham_line(origin, target):
                if not dungeon.is_in_bounds(point):
                    break
                visible.add(point)
                if dungeon.tile_at(point) == WALL:
                    break

    return visible
