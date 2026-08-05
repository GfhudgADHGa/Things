"""Closest pair of points: O(n log n) divide-and-conquer (the textbook
algorithm -- split by x, recurse on each half, then check only the
narrow vertical strip around the split line where a closer cross-half
pair could possibly exist), verified against the O(n^2) brute-force
pairwise-distance scan it's meant to outperform.
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from .primitives import Point


def _dist(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def brute_force_closest_pair(points: List[Point]) -> Tuple[Tuple[Point, Point], float]:
    if len(points) < 2:
        raise ValueError("need at least 2 points")
    best_pair = (points[0], points[1])
    best_dist = _dist(points[0], points[1])
    n = len(points)
    for i in range(n):
        for j in range(i + 1, n):
            d = _dist(points[i], points[j])
            if d < best_dist:
                best_dist = d
                best_pair = (points[i], points[j])
    return best_pair, best_dist


def closest_pair(points: List[Point]) -> Tuple[Tuple[Point, Point], float]:
    if len(points) < 2:
        raise ValueError("need at least 2 points")

    seen = {}
    for p in points:
        if p in seen:
            return (p, p), 0.0  # an exact duplicate is trivially the closest possible pair
        seen[p] = True

    pts_x = sorted(points)
    pts_y = sorted(points, key=lambda p: p[1])
    return _closest_pair_rec(pts_x, pts_y)


def _closest_pair_rec(pts_x: List[Point], pts_y: List[Point]) -> Tuple[Tuple[Point, Point], float]:
    n = len(pts_x)
    if n <= 3:
        return brute_force_closest_pair(pts_x)

    mid = n // 2
    mid_x = pts_x[mid][0]
    left_x, right_x = pts_x[:mid], pts_x[mid:]
    left_set = set(left_x)
    left_y = [p for p in pts_y if p in left_set]
    right_y = [p for p in pts_y if p not in left_set]

    left_pair, left_dist = _closest_pair_rec(left_x, left_y)
    right_pair, right_dist = _closest_pair_rec(right_x, right_y)
    best_pair, best_dist = (left_pair, left_dist) if left_dist <= right_dist else (right_pair, right_dist)

    # Any closer cross-boundary pair must both lie within best_dist of the
    # split line -- and among points sorted by y, at most a handful of
    # candidates within that strip can possibly be closer (a well-known
    # packing argument: past the 7th-next point in y-order, the two
    # points can't both fit within a best_dist x best_dist box anymore).
    strip = [p for p in pts_y if abs(p[0] - mid_x) < best_dist]
    for i in range(len(strip)):
        for j in range(i + 1, min(i + 7, len(strip))):
            d = _dist(strip[i], strip[j])
            if d < best_dist:
                best_dist = d
                best_pair = (strip[i], strip[j])
    return best_pair, best_dist
