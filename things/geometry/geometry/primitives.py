"""The one primitive nearly everything else in this package is built
from: the 2D cross product of (a-o) and (b-o), whose sign says which way
you turn going from o->a to o->b. Positive: counterclockwise (b is to
the left of ray o->a). Negative: clockwise. Zero: collinear.
"""
from __future__ import annotations

from typing import Tuple

Point = Tuple[float, float]


def cross(o: Point, a: Point, b: Point) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def orientation(o: Point, a: Point, b: Point) -> int:
    c = cross(o, a, b)
    if c > 0:
        return 1
    if c < 0:
        return -1
    return 0
