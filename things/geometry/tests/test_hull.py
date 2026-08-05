"""The correctness proof: three independently-derived algorithms
(monotone-chain sweep, gift-wrapping march, brute-force edge testing)
must agree on the hull vertex set across randomized point clouds --
along with hand-picked shapes and the degenerate cases (collinear
points, fewer than 3 points) where hull algorithms most often have
off-by-one bugs.
"""
import random

import pytest

from geometry.hull import brute_force_hull_vertices, gift_wrapping, graham_scan


def _all_agree(points):
    gs = set(graham_scan(points))
    gw = set(gift_wrapping(points))
    bf = brute_force_hull_vertices(points)
    return gs == gw == bf, (gs, gw, bf)


def test_triangle():
    pts = [(0, 0), (4, 0), (2, 3)]
    agree, (gs, gw, bf) = _all_agree(pts)
    assert agree
    assert gs == set(pts)


def test_square_with_an_interior_point():
    pts = [(0, 0), (4, 0), (4, 4), (0, 4), (2, 2)]
    agree, (gs, gw, bf) = _all_agree(pts)
    assert agree
    assert gs == {(0, 0), (4, 0), (4, 4), (0, 4)}  # interior point excluded


def test_collinear_points_on_an_edge_are_excluded():
    # (2,0) lies exactly on the edge from (0,0) to (4,0) -- a "pass
    # through" point, not a hull vertex, by this package's convention
    pts = [(0, 0), (2, 0), (4, 0), (4, 4), (0, 4)]
    agree, (gs, gw, bf) = _all_agree(pts)
    assert agree
    assert (2, 0) not in gs


def test_all_points_collinear():
    pts = [(0, 0), (1, 1), (2, 2), (3, 3)]
    assert set(graham_scan(pts)) == {(0, 0), (3, 3)}
    assert brute_force_hull_vertices(pts) == {(0, 0), (3, 3)}


def test_duplicate_points_are_deduplicated():
    pts = [(0, 0), (0, 0), (4, 0), (4, 4), (0, 4)]
    assert set(graham_scan(pts)) == {(0, 0), (4, 0), (4, 4), (0, 4)}


def test_two_points():
    pts = [(0, 0), (5, 5)]
    assert set(graham_scan(pts)) == {(0, 0), (5, 5)}


def test_single_point():
    assert graham_scan([(1, 1)]) == [(1, 1)]


def test_graham_scan_output_is_in_valid_ccw_order():
    pts = [(0, 0), (4, 0), (4, 4), (0, 4)]
    hull = graham_scan(pts)
    n = len(hull)
    # every consecutive triple must be a strict left turn (CCW), cyclically
    from geometry.primitives import cross
    for i in range(n):
        o, a, b = hull[i], hull[(i + 1) % n], hull[(i + 2) % n]
        assert cross(o, a, b) > 0


@pytest.mark.parametrize("seed", range(300))
def test_random_point_clouds_all_three_methods_agree(seed):
    rng = random.Random(seed)
    n = rng.randint(3, 25)
    # coarse coordinates increase the chance of hitting collinear/
    # duplicate edge cases, not just generic position
    pts = [(rng.randint(-8, 8), rng.randint(-8, 8)) for _ in range(n)]
    agree, (gs, gw, bf) = _all_agree(pts)
    assert agree, f"seed={seed}: graham={gs} gift={gw} brute={bf}"


@pytest.mark.parametrize("seed", range(100))
def test_random_points_on_a_circle_all_three_methods_agree(seed):
    # points on a circle are all hull vertices (strictly convex position,
    # no interior points, no collinear points) -- a different structural
    # case than random scattered clouds
    import math
    rng = random.Random(seed + 5000)
    n = rng.randint(3, 15)
    pts = [
        (round(10 * math.cos(2 * math.pi * i / n), 6), round(10 * math.sin(2 * math.pi * i / n), 6))
        for i in range(n)
    ]
    agree, (gs, gw, bf) = _all_agree(pts)
    assert agree
    assert len(gs) == n  # every point on a circle is a hull vertex
