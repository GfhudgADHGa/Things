"""A* pathfinding on the dungeon grid, 8-directional with uniform step
cost. Replaces the old "just move toward the target, ignoring walls in
between" heuristic, which works fine in open rooms but gets a monster
stuck pressed against a wall whenever the straight-line direction toward
the player isn't actually walkable (a monster on the far side of a
corridor bend, for instance).
"""
from __future__ import annotations

import heapq
import itertools
from typing import List, Optional, Set

from .dungeon import Dungeon
from .geometry import Point

_NEIGHBOR_OFFSETS = [
    Point(dx, dy)
    for dx in (-1, 0, 1)
    for dy in (-1, 0, 1)
    if not (dx == 0 and dy == 0)
]


def _heuristic(a: Point, b: Point) -> int:
    """Chebyshev distance: admissible and consistent for 8-directional
    movement where every step (including diagonal) costs 1.
    """
    return max(abs(a.x - b.x), abs(a.y - b.y))


def _neighbors(dungeon: Dungeon, point: Point, blocked: Set[Point], goal: Point):
    for offset in _NEIGHBOR_OFFSETS:
        candidate = point + offset
        if not dungeon.is_walkable(candidate):
            continue
        if candidate in blocked and candidate != goal:
            continue
        yield candidate


def find_path(
    dungeon: Dungeon, start: Point, goal: Point, blocked: Set[Point]
) -> Optional[List[Point]]:
    """Returns the shortest path from start to goal (inclusive of both
    endpoints) as a list of Points, or None if no path exists. `blocked`
    cells are avoided except for the goal itself, so a path can always be
    found *toward* an occupied target even though the search won't step
    onto any other occupied cell along the way.
    """
    if start == goal:
        return [start]

    tiebreak = itertools.count()
    open_heap = [(_heuristic(start, goal), 0, next(tiebreak), start)]
    came_from: dict = {}
    g_score = {start: 0}
    closed: Set[Point] = set()

    while open_heap:
        _, g, _, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        closed.add(current)

        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        for neighbor in _neighbors(dungeon, current, blocked, goal):
            tentative_g = g + 1
            if tentative_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = tentative_g
                came_from[neighbor] = current
                f = tentative_g + _heuristic(neighbor, goal)
                heapq.heappush(open_heap, (f, tentative_g, next(tiebreak), neighbor))

    return None
