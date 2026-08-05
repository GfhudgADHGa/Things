from roguelike.dungeon import generate_dungeon
from roguelike.geometry import Point
from roguelike.pathfinding import find_path


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


def test_path_to_self_is_single_point():
    d = open_dungeon()
    p = Point(5, 5)
    assert find_path(d, p, p, set()) == [p]


def test_path_starts_and_ends_correctly():
    d = open_dungeon()
    start, goal = Point(2, 2), Point(10, 10)
    path = find_path(d, start, goal, set())
    assert path[0] == start
    assert path[-1] == goal


def test_path_is_contiguous_8_directional_steps():
    d = open_dungeon()
    path = find_path(d, Point(2, 2), Point(12, 8), set())
    for a, b in zip(path, path[1:]):
        assert abs(a.x - b.x) <= 1
        assert abs(a.y - b.y) <= 1
        assert a != b


def test_path_length_matches_chebyshev_distance_in_open_space():
    # with unobstructed 8-directional movement, the optimal path length is
    # exactly the Chebyshev distance (diagonal moves cover both axes at once)
    d = open_dungeon()
    start, goal = Point(2, 2), Point(10, 8)
    path = find_path(d, start, goal, set())
    chebyshev = max(abs(goal.x - start.x), abs(goal.y - start.y))
    assert len(path) - 1 == chebyshev


def test_path_never_steps_on_a_wall():
    d = open_dungeon()
    for y in range(1, 15):
        d.tiles[y][10] = "#"
    path = find_path(d, Point(5, 5), Point(15, 5), set())
    assert path is not None
    for p in path:
        assert d.is_walkable(p)


def test_path_never_steps_on_a_blocked_cell_except_the_goal():
    d = open_dungeon()
    blocked = {Point(6, 5), Point(6, 4), Point(6, 6), Point(5, 4), Point(5, 6)}
    path = find_path(d, Point(5, 5), Point(10, 5), blocked)
    assert path is not None
    for p in path[:-1]:
        assert p not in blocked


def test_path_to_a_blocked_goal_still_succeeds():
    # the goal square itself is exempt from the blocked check -- callers
    # rely on this to path toward an occupied target (the player)
    d = open_dungeon()
    goal = Point(10, 5)
    path = find_path(d, Point(5, 5), goal, blocked={goal})
    assert path is not None
    assert path[-1] == goal


def test_no_path_when_start_fully_enclosed():
    d = open_dungeon()
    start = Point(5, 5)
    blocked = {
        Point(start.x + dx, start.y + dy)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        if not (dx == 0 and dy == 0)
    }
    assert find_path(d, start, Point(15, 15), blocked) is None


def test_no_path_when_goal_is_unreachable_behind_a_sealed_wall():
    d = open_dungeon()
    for x in range(20):
        d.tiles[10][x] = "#"  # a solid wall spanning the whole width, no gap
    path = find_path(d, Point(5, 5), Point(5, 15), set())
    assert path is None


def test_path_routes_around_a_wall_with_a_gap():
    d = open_dungeon()
    for y in range(1, 15):
        d.tiles[y][10] = "#"
    # gap at y=15..18
    path = find_path(d, Point(5, 5), Point(15, 5), set())
    assert path is not None
    # the path must pass through the gap (x=10 only walkable at y >= 15)
    crossing_points = [p for p in path if p.x == 10]
    assert crossing_points
    assert all(p.y >= 15 for p in crossing_points)


def test_path_is_deterministic():
    d = open_dungeon()
    a = find_path(d, Point(2, 2), Point(15, 15), set())
    b = find_path(d, Point(2, 2), Point(15, 15), set())
    assert a == b
