"""Minimal 2D vector math. Coordinates match pixel/screen space: y increases
downward, so gravity is a positive-y acceleration.
"""
from __future__ import annotations

import math


class Vec2:
    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y

    def __add__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x + o.x, self.y + o.y)

    def __sub__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x - o.x, self.y - o.y)

    def __neg__(self) -> "Vec2":
        return Vec2(-self.x, -self.y)

    def __mul__(self, scalar: float) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def __eq__(self, o) -> bool:
        return isinstance(o, Vec2) and self.x == o.x and self.y == o.y

    def __repr__(self) -> str:
        return f"Vec2({self.x!r}, {self.y!r})"

    def dot(self, o: "Vec2") -> float:
        return self.x * o.x + self.y * o.y

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalized(self) -> "Vec2":
        length = self.length()
        if length == 0:
            return Vec2(0, 0)
        return Vec2(self.x / length, self.y / length)
