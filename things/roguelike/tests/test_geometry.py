from roguelike.geometry import Point, Rect


def test_point_add():
    assert Point(1, 2) + Point(3, 4) == Point(4, 6)


def test_point_distance_squared():
    assert Point(0, 0).distance_squared(Point(3, 4)) == 25


def test_rect_center():
    r = Rect(0, 0, 4, 4)
    assert r.center == Point(2, 2)


def test_rect_intersects_overlapping():
    a = Rect(0, 0, 5, 5)
    b = Rect(3, 3, 8, 8)
    assert a.intersects(b)
    assert b.intersects(a)


def test_rect_intersects_disjoint():
    a = Rect(0, 0, 2, 2)
    b = Rect(10, 10, 12, 12)
    assert not a.intersects(b)


def test_rect_interior_points_excludes_border():
    r = Rect(0, 0, 2, 2)
    points = set(r.interior_points())
    assert points == {Point(1, 1)}
