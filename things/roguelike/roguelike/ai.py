"""Simple monster AI: chase the player when visible, otherwise idle."""
from __future__ import annotations

import random
from typing import Optional

from .dungeon import Dungeon
from .geometry import Point
from .entities import Monster, Player


def step_towards(dungeon: Dungeon, start: Point, target: Point, blocked: set) -> Point:
    """Returns the best single-tile move from start towards target.

    Falls back to staying in place if every direction is blocked.
    """
    best_move = start
    best_distance = start.distance_squared(target)

    candidates = [
        Point(start.x + dx, start.y + dy)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        if not (dx == 0 and dy == 0)
    ]
    for candidate in candidates:
        if not dungeon.is_walkable(candidate):
            continue
        if candidate in blocked:
            continue
        distance = candidate.distance_squared(target)
        if distance < best_distance:
            best_distance = distance
            best_move = candidate

    return best_move


def take_monster_turn(
    monster: Monster,
    dungeon: Dungeon,
    player: Player,
    visible_to_monster: set,
    occupied: set,
    rng: Optional[random.Random] = None,
) -> Optional[Point]:
    """Decides the monster's move for this turn.

    Returns the point it wants to move into, or None if it attacks in place
    (already adjacent) or does nothing. Does not mutate monster position;
    the caller applies the move after checking for a player collision.
    """
    rng = rng or random
    if player.position in visible_to_monster:
        monster.aggro = True

    if not monster.aggro:
        if rng.random() < 0.3:
            dx, dy = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            candidate = Point(monster.position.x + dx, monster.position.y + dy)
            if dungeon.is_walkable(candidate) and candidate not in occupied:
                return candidate
        return None

    if monster.position.distance_squared(player.position) <= 2:
        return player.position  # signals "attack"

    blocked = occupied - {monster.position}
    return step_towards(dungeon, monster.position, player.position, blocked)
