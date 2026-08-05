"""Segment intersection, two independent derivations:

- `segments_intersect`: the standard O(1) orientation test -- two
  segments cross iff each one's endpoints straddle the other (opposite
  orientations relative to it), with explicit collinear-overlap
  handling for the degenerate on-the-line cases.
- `segments_intersect_parametric`: solve p1 + t(p2-p1) = p3 + u(p4-p3)
  directly as a 2x2 linear system (Cramer's rule) and check whether the
  solution's t and u both land in [0, 1] -- linear algebra, not
  combinatorial orientation testing, for a genuinely different
  derivation of the same yes/no answer.
"""
from __future__ import annotations

from .primitives import Point, orientation


def _on_segment(p: Point, q: Point, r: Point) -> bool:
    """True if q lies within p and r's bounding box, given p, q, r are
    already known to be collinear."""
    return min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and min(p[1], r[1]) <= q[1] <= max(p[1], r[1])


def segments_intersect(p1: Point, p2: Point, p3: Point, p4: Point) -> bool:
    o1 = orientation(p1, p2, p3)
    o2 = orientation(p1, p2, p4)
    o3 = orientation(p3, p4, p1)
    o4 = orientation(p3, p4, p2)

    if o1 != o2 and o3 != o4:
        return True

    if o1 == 0 and _on_segment(p1, p3, p2):
        return True
    if o2 == 0 and _on_segment(p1, p4, p2):
        return True
    if o3 == 0 and _on_segment(p3, p1, p4):
        return True
    if o4 == 0 and _on_segment(p3, p2, p4):
        return True

    return False


def segments_intersect_parametric(p1: Point, p2: Point, p3: Point, p4: Point) -> bool:
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0:
        if orientation(p1, p2, p3) != 0:
            return False  # parallel and not collinear: can never intersect
        # collinear: overlap iff any endpoint of one segment falls
        # within the other's bounding box
        return (
            _on_segment(p1, p3, p2) or _on_segment(p1, p4, p2)
            or _on_segment(p3, p1, p4) or _on_segment(p3, p2, p4)
        )

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = ((x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)) / denom
    return 0 <= t <= 1 and 0 <= u <= 1
