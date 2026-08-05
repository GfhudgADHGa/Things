"""Small geometry helpers shared by dungeon generation and FOV."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Tuple


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def __add__(self, o: "Point") -> "Point":
        return Point(self.x + o.x, self.y + o.y)

    def distance_squared(self, o: "Point") -> int:
        return (self.x - o.x) ** 2 + (self.y - o.y) ** 2

    def as_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)


DIRECTIONS = {
    "n": Point(0, -1),
    "s": Point(0, 1),
    "e": Point(1, 0),
    "w": Point(-1, 0),
    "ne": Point(1, -1),
    "nw": Point(-1, -1),
    "se": Point(1, 1),
    "sw": Point(-1, 1),
}


@dataclass(frozen=True)
class Rect:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def center(self) -> Point:
        return Point((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    def intersects(self, other: "Rect") -> bool:
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )

    def interior_points(self) -> Iterator[Point]:
        for y in range(self.y1 + 1, self.y2):
            for x in range(self.x1 + 1, self.x2):
                yield Point(x, y)
