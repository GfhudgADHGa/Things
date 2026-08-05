"""Point-in-polygon, two independent derivations:

- Ray casting: cast a ray from the point off to one side and count how
  many times it crosses the polygon's boundary; an odd count means
  inside (the classic parity argument -- crossing a closed boundary an
  odd number of times means you end up on the opposite side from where
  you started).
- Winding number: sum the signed angular contribution of each edge as
  seen from the point; a nonzero total means the boundary wraps around
  the point at least once (Sunday's algorithm, tracking crossings of a
  horizontal ray without computing any actual angles).

These come from genuinely different geometric ideas -- parity of
crossings vs. total signed rotation -- despite answering the same
question, which is what makes checking them against each other a real
cross-check rather than two copies of the same reasoning.
"""
from __future__ import annotations

from typing import List

from .primitives import Point, cross


def point_in_polygon_ray_casting(point: Point, polygon: List[Point]) -> bool:
    x, y = point
    n = len(polygon)
    inside = False
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            x_intersect = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < x_intersect:
                inside = not inside
    return inside


def point_in_polygon_winding_number(point: Point, polygon: List[Point]) -> bool:
    x, y = point
    n = len(polygon)
    winding = 0
    for i in range(n):
        p1, p2 = polygon[i], polygon[(i + 1) % n]
        if p1[1] <= y:
            if p2[1] > y and cross(p1, p2, point) > 0:
                winding += 1
        else:
            if p2[1] <= y and cross(p1, p2, point) < 0:
                winding -= 1
    return winding != 0
