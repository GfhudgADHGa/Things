"""Convex hull, computed three genuinely independent ways:

- `graham_scan`: Andrew's monotone chain -- sort by x (then y), build
  the lower chain and upper chain separately by a stack that pops
  whenever the last three points don't turn left, O(n log n).
- `gift_wrapping`: Jarvis march -- starting from the guaranteed-extreme
  leftmost point, repeatedly find the most counterclockwise next point,
  O(nh) where h is the hull size.
- `brute_force_hull_vertices`: for every ordered pair of input points,
  check whether *every other point* lies on one side of that line (or
  exactly on it) -- if so, that pair is a hull edge. O(n^3), and
  completely different in kind from the two sweep-based algorithms
  above: it never sorts anything or wraps around anything, it just
  directly tests the defining property of a hull edge.

All three agree on the *set* of hull vertices (checked in
test_hull.py); collinear points lying exactly on a hull edge (not at a
corner) are excluded from all three by convention, not just some of
them.
"""
from __future__ import annotations

from typing import List, Set

from .primitives import Point, cross


def graham_scan(points: List[Point]) -> List[Point]:
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def build_half(ordered: List[Point]) -> List[Point]:
        half: List[Point] = []
        for p in ordered:
            while len(half) >= 2 and cross(half[-2], half[-1], p) <= 0:
                half.pop()
            half.append(p)
        return half

    lower = build_half(pts)
    upper = build_half(list(reversed(pts)))
    return lower[:-1] + upper[:-1]


def gift_wrapping(points: List[Point]) -> List[Point]:
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    start = pts[0]
    hull: List[Point] = []
    current = start
    while True:
        hull.append(current)
        candidate = pts[0] if pts[0] != current else pts[1]
        for p in pts:
            if p == current or p == candidate:
                continue
            c = cross(current, candidate, p)
            if c < 0:
                candidate = p
            elif c == 0:
                # p is collinear with current->candidate: prefer whichever
                # is farther, so the near one gets excluded as a
                # pass-through point, not kept as a spurious "vertex"
                if _dist2(current, p) > _dist2(current, candidate):
                    candidate = p
        current = candidate
        if current == start:
            break
        if len(hull) > len(pts):
            raise RuntimeError("gift wrapping failed to terminate (should be impossible)")
    return hull


def _dist2(a: Point, b: Point) -> float:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def brute_force_hull_vertices(points: List[Point]) -> Set[Point]:
    """For every ordered pair (a, b), check whether every *other* point
    lies on one consistent side of the line through a and b (points
    exactly on the line don't count against either side). If so, that
    line is a hull edge -- but naively adding just `a` and `b` as
    vertices is wrong whenever a third point also lies exactly on that
    same line: every sub-pair among 3+ collinear points on one hull edge
    independently passes the same "all others on one side" test, which
    would incorrectly report the *middle* points as hull vertices too.
    (This is exactly the bug the first version of this function had --
    caught because graham_scan and gift_wrapping, agreeing with each
    other, disagreed with this function on inputs with 3+ collinear
    points sharing a hull edge; see test_hull.py.) The fix: once a line
    is confirmed to be a hull edge, only its two *extreme* points
    (by projection onto the line's own direction) count as vertices --
    anything collinear and strictly between them is a pass-through
    point, not a corner.
    """
    pts = list(set(points))
    n = len(pts)
    if n <= 2:
        return set(pts)
    hull_points: Set[Point] = set()
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            a, b = pts[i], pts[j]
            side = None
            valid = True
            collinear_pts = [a, b]
            for k in range(n):
                if k == i or k == j:
                    continue
                c = cross(a, b, pts[k])
                if c == 0:
                    collinear_pts.append(pts[k])
                    continue
                positive = c > 0
                if side is None:
                    side = positive
                elif positive != side:
                    valid = False
                    break
            if valid and side is not None:
                dx, dy = b[0] - a[0], b[1] - a[1]

                def _proj(p: Point) -> float:
                    return (p[0] - a[0]) * dx + (p[1] - a[1]) * dy

                hull_points.add(min(collinear_pts, key=_proj))
                hull_points.add(max(collinear_pts, key=_proj))
    if n >= 3 and not hull_points:
        # every point is collinear -- no 2D hull; the two extremes are
        # the "hull" in the degenerate 1D sense
        return {min(pts), max(pts)}
    return hull_points
