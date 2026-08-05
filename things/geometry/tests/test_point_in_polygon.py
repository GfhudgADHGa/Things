import math
import random

import pytest

from geometry.hull import graham_scan
from geometry.point_in_polygon import point_in_polygon_ray_casting, point_in_polygon_winding_number

SQUARE = [(0, 0), (4, 0), (4, 4), (0, 4)]


def test_point_clearly_inside():
    assert point_in_polygon_ray_casting((2, 2), SQUARE) is True
    assert point_in_polygon_winding_number((2, 2), SQUARE) is True


def test_point_clearly_outside():
    assert point_in_polygon_ray_casting((10, 10), SQUARE) is False
    assert point_in_polygon_winding_number((10, 10), SQUARE) is False


def test_point_outside_but_within_bounding_box():
    # an L-shaped / non-convex polygon so a naive "inside the bounding
    # box" check would get this wrong
    L_shape = [(0, 0), (4, 0), (4, 2), (2, 2), (2, 4), (0, 4)]
    inside_notch = (3, 3)  # inside the bounding box, but in the cut-out notch
    assert point_in_polygon_ray_casting(inside_notch, L_shape) is False
    assert point_in_polygon_winding_number(inside_notch, L_shape) is False


def test_point_inside_l_shape_body():
    L_shape = [(0, 0), (4, 0), (4, 2), (2, 2), (2, 4), (0, 4)]
    assert point_in_polygon_ray_casting((1, 1), L_shape) is True
    assert point_in_polygon_winding_number((1, 1), L_shape) is True


def test_triangle():
    triangle = [(0, 0), (4, 0), (2, 4)]
    assert point_in_polygon_ray_casting((2, 1), triangle) is True
    assert point_in_polygon_ray_casting((2, 5), triangle) is False


@pytest.mark.parametrize("seed", range(500))
def test_ray_casting_matches_winding_number_random_convex_polygons(seed):
    rng = random.Random(seed)
    n = rng.randint(3, 12)
    raw = [(rng.uniform(-10, 10), rng.uniform(-10, 10)) for _ in range(n)]
    polygon = graham_scan(raw)
    if len(polygon) < 3:
        return
    point = (rng.uniform(-15, 15), rng.uniform(-15, 15))
    a = point_in_polygon_ray_casting(point, polygon)
    b = point_in_polygon_winding_number(point, polygon)
    assert a == b, f"seed={seed}: polygon={polygon} point={point} ray={a} winding={b}"


@pytest.mark.parametrize("seed", range(200))
def test_ray_casting_matches_winding_number_star_shaped_polygons(seed):
    # a non-convex star polygon: alternating far/near vertices around a
    # circle -- a structurally different shape than the convex hulls above
    rng = random.Random(seed + 7000)
    n = rng.randint(5, 10)
    polygon = []
    for i in range(n):
        angle = 2 * math.pi * i / n
        radius = 10.0 if i % 2 == 0 else 4.0
        polygon.append((radius * math.cos(angle), radius * math.sin(angle)))
    point = (rng.uniform(-12, 12), rng.uniform(-12, 12))
    a = point_in_polygon_ray_casting(point, polygon)
    b = point_in_polygon_winding_number(point, polygon)
    assert a == b, f"seed={seed}: point={point} ray={a} winding={b}"
