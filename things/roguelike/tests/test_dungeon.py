from roguelike.dungeon import FLOOR, STAIRS_DOWN, STAIRS_UP, WALL, generate_dungeon
from roguelike.geometry import Point


def test_generate_dungeon_dimensions():
    d = generate_dungeon(60, 20, seed=1)
    assert d.width == 60
    assert d.height == 20
    assert len(d.tiles) == 20
    assert all(len(row) == 60 for row in d.tiles)


def test_generate_dungeon_has_multiple_rooms():
    d = generate_dungeon(60, 20, seed=1)
    assert len(d.rooms) >= 2


def test_generate_dungeon_is_deterministic():
    d1 = generate_dungeon(60, 20, seed=42)
    d2 = generate_dungeon(60, 20, seed=42)
    assert d1.tiles == d2.tiles
    assert d1.rooms == d2.rooms


def test_different_seeds_produce_different_layouts():
    d1 = generate_dungeon(60, 20, seed=1)
    d2 = generate_dungeon(60, 20, seed=2)
    assert d1.tiles != d2.tiles


def test_stairs_are_placed_and_walkable():
    d = generate_dungeon(60, 20, seed=5)
    assert d.tile_at(d.stairs_up) == STAIRS_UP
    assert d.tile_at(d.stairs_down) == STAIRS_DOWN
    assert d.is_walkable(d.stairs_up)
    assert d.is_walkable(d.stairs_down)


def test_stairs_up_and_down_differ_with_multiple_rooms():
    d = generate_dungeon(60, 20, seed=5)
    assert d.stairs_up != d.stairs_down


def test_border_is_wall():
    d = generate_dungeon(30, 15, seed=3)
    for x in range(30):
        assert d.tile_at(Point(x, 0)) == WALL
        assert d.tile_at(Point(x, 14)) == WALL
    for y in range(15):
        assert d.tile_at(Point(0, y)) == WALL
        assert d.tile_at(Point(29, y)) == WALL


def test_rooms_are_reachable_from_first_room():
    """Every floor tile should be reachable from the start via flood fill."""
    d = generate_dungeon(60, 20, seed=7)
    start = d.stairs_up
    seen = {start}
    stack = [start]
    while stack:
        current = stack.pop()
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = Point(current.x + dx, current.y + dy)
            if neighbor in seen:
                continue
            if d.is_walkable(neighbor):
                seen.add(neighbor)
                stack.append(neighbor)

    all_floor = {
        Point(x, y)
        for y in range(d.height)
        for x in range(d.width)
        if d.tile_at(Point(x, y)) != WALL
    }
    assert seen == all_floor


def test_out_of_bounds_is_not_walkable():
    d = generate_dungeon(30, 15, seed=1)
    assert not d.is_walkable(Point(-1, 0))
    assert not d.is_walkable(Point(1000, 1000))
