"""Procedural dungeon generation: rooms connected by L-shaped corridors."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List

from .geometry import Point, Rect

WALL = "#"
FLOOR = "."
STAIRS_DOWN = ">"
STAIRS_UP = "<"


@dataclass
class Dungeon:
    width: int
    height: int
    tiles: List[List[str]] = field(default_factory=list)
    rooms: List[Rect] = field(default_factory=list)
    stairs_down: Point = None
    stairs_up: Point = None

    def is_in_bounds(self, p: Point) -> bool:
        return 0 <= p.x < self.width and 0 <= p.y < self.height

    def is_walkable(self, p: Point) -> bool:
        return self.is_in_bounds(p) and self.tiles[p.y][p.x] != WALL

    def tile_at(self, p: Point) -> str:
        if not self.is_in_bounds(p):
            return WALL
        return self.tiles[p.y][p.x]


def _carve_room(tiles: List[List[str]], room: Rect) -> None:
    for y in range(room.y1, room.y2 + 1):
        for x in range(room.x1, room.x2 + 1):
            tiles[y][x] = FLOOR


def _carve_h_corridor(tiles: List[List[str]], x1: int, x2: int, y: int) -> None:
    for x in range(min(x1, x2), max(x1, x2) + 1):
        tiles[y][x] = FLOOR


def _carve_v_corridor(tiles: List[List[str]], y1: int, y2: int, x: int) -> None:
    for y in range(min(y1, y2), max(y1, y2) + 1):
        tiles[y][x] = FLOOR


def generate_dungeon(
    width: int,
    height: int,
    seed: int,
    max_rooms: int = 12,
    min_room_size: int = 4,
    max_room_size: int = 9,
) -> Dungeon:
    rng = random.Random(seed)
    tiles = [[WALL for _ in range(width)] for _ in range(height)]
    rooms: List[Rect] = []

    for _ in range(max_rooms):
        w = rng.randint(min_room_size, max_room_size)
        h = rng.randint(min_room_size, max_room_size)
        x = rng.randint(1, max(1, width - w - 2))
        y = rng.randint(1, max(1, height - h - 2))
        new_room = Rect(x, y, x + w, y + h)

        # pad by 1 so rooms never touch (leaves a wall between them)
        padded = Rect(new_room.x1 - 1, new_room.y1 - 1, new_room.x2 + 1, new_room.y2 + 1)
        if any(padded.intersects(r) for r in rooms):
            continue

        _carve_room(tiles, new_room)

        if rooms:
            prev_center = rooms[-1].center
            new_center = new_room.center
            if rng.random() < 0.5:
                _carve_h_corridor(tiles, prev_center.x, new_center.x, prev_center.y)
                _carve_v_corridor(tiles, prev_center.y, new_center.y, new_center.x)
            else:
                _carve_v_corridor(tiles, prev_center.y, new_center.y, prev_center.x)
                _carve_h_corridor(tiles, prev_center.x, new_center.x, new_center.y)

        rooms.append(new_room)

    dungeon = Dungeon(width=width, height=height, tiles=tiles, rooms=rooms)

    if rooms:
        dungeon.stairs_up = rooms[0].center
        dungeon.stairs_down = rooms[-1].center
        tiles[dungeon.stairs_up.y][dungeon.stairs_up.x] = STAIRS_UP
        tiles[dungeon.stairs_down.y][dungeon.stairs_down.x] = STAIRS_DOWN

    return dungeon
