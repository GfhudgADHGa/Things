from roguelike.dungeon import generate_dungeon
from roguelike.fov import bresenham_line, compute_fov
from roguelike.geometry import Point


def test_bresenham_line_horizontal():
    line = bresenham_line(Point(0, 0), Point(3, 0))
    assert line == [Point(0, 0), Point(1, 0), Point(2, 0), Point(3, 0)]


def test_bresenham_line_diagonal():
    line = bresenham_line(Point(0, 0), Point(3, 3))
    assert line[0] == Point(0, 0)
    assert line[-1] == Point(3, 3)
    assert len(line) == 4


def test_bresenham_line_single_point():
    assert bresenham_line(Point(2, 2), Point(2, 2)) == [Point(2, 2)]


def test_fov_includes_origin():
    d = generate_dungeon(30, 15, seed=1)
    origin = d.stairs_up
    visible = compute_fov(d, origin, radius=5)
    assert origin in visible


def test_fov_is_bounded_by_radius():
    d = generate_dungeon(60, 30, seed=2)
    for y in range(30):
        d.tiles[y] = ["."] * 60  # open floor everywhere so only radius limits visibility
    origin = Point(30, 15)
    visible = compute_fov(d, origin, radius=3)
    far_point = Point(30, 25)
    assert far_point not in visible
    assert Point(30, 17) in visible


def test_fov_blocked_by_wall():
    d = generate_dungeon(20, 10, seed=1)
    # build a small isolated open room surrounded by walls we control directly
    for y in range(10):
        d.tiles[y] = ["#"] * 20
    for y in range(2, 8):
        for x in range(2, 8):
            d.tiles[y][x] = "."
    origin = Point(3, 5)
    visible = compute_fov(d, origin, radius=20)
    # a point far outside the room, beyond the walls, must not be visible
    assert Point(15, 5) not in visible
    # but the wall immediately bounding the room to the east should be
    # visible (you can see the wall that blocks your view)
    assert Point(8, 5) in visible
