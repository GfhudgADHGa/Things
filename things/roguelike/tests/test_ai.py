import random

from roguelike import ai
from roguelike.dungeon import generate_dungeon
from roguelike.entities import make_monster, make_player
from roguelike.geometry import Point


def open_dungeon(width=20, height=20, seed=1):
    d = generate_dungeon(width, height, seed=seed)
    for y in range(height):
        d.tiles[y] = ["."] * width
    for x in range(width):
        d.tiles[0][x] = "#"
        d.tiles[height - 1][x] = "#"
    for y in range(height):
        d.tiles[y][0] = "#"
        d.tiles[y][width - 1] = "#"
    return d


def test_step_towards_moves_closer():
    d = open_dungeon()
    start = Point(5, 5)
    target = Point(10, 5)
    move = ai.step_towards(d, start, target, blocked=set())
    assert move.distance_squared(target) < start.distance_squared(target)


def test_step_towards_avoids_blocked_tiles():
    d = open_dungeon()
    start = Point(5, 5)
    target = Point(6, 5)
    # block every tile that would be a strict improvement except one
    blocked = {Point(6, 5), Point(6, 4), Point(6, 6)}
    move = ai.step_towards(d, start, target, blocked)
    assert move not in blocked


def test_step_towards_stays_when_fully_surrounded():
    d = open_dungeon()
    start = Point(5, 5)
    target = Point(10, 5)
    blocked = {
        Point(start.x + dx, start.y + dy)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        if not (dx == 0 and dy == 0)
    }
    move = ai.step_towards(d, start, target, blocked)
    assert move == start


def test_monster_not_aggro_when_player_not_visible():
    d = open_dungeon()
    monster = make_monster("rat", Point(2, 2))
    player = make_player(Point(15, 15))
    rng = random.Random(0)
    ai.take_monster_turn(monster, d, player, visible_to_monster=set(), occupied=set(), rng=rng)
    assert not monster.aggro


def test_monster_becomes_aggro_when_player_visible():
    d = open_dungeon()
    monster = make_monster("rat", Point(2, 2))
    player = make_player(Point(10, 2))
    rng = random.Random(0)
    ai.take_monster_turn(
        monster, d, player, visible_to_monster={player.position}, occupied=set(), rng=rng
    )
    assert monster.aggro


def test_aggro_monster_moves_toward_player():
    d = open_dungeon()
    monster = make_monster("rat", Point(2, 2))
    monster.aggro = True
    player = make_player(Point(10, 2))
    rng = random.Random(0)
    move = ai.take_monster_turn(
        monster, d, player, visible_to_monster={player.position}, occupied={player.position}, rng=rng
    )
    assert move is not None
    assert move.distance_squared(player.position) < monster.position.distance_squared(player.position)


def test_aggro_monster_adjacent_to_player_signals_attack():
    d = open_dungeon()
    monster = make_monster("rat", Point(9, 2))
    monster.aggro = True
    player = make_player(Point(10, 2))
    rng = random.Random(0)
    move = ai.take_monster_turn(
        monster, d, player, visible_to_monster={player.position}, occupied={player.position}, rng=rng
    )
    assert move == player.position
