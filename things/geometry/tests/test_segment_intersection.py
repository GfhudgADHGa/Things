import random

import pytest

from geometry.segment_intersection import segments_intersect, segments_intersect_parametric


def test_crossing_segments():
    assert segments_intersect((0, 0), (4, 4), (0, 4), (4, 0)) is True
    assert segments_intersect_parametric((0, 0), (4, 4), (0, 4), (4, 0)) is True


def test_non_crossing_segments():
    assert segments_intersect((0, 0), (1, 1), (5, 5), (6, 6)) is False
    assert segments_intersect_parametric((0, 0), (1, 1), (5, 5), (6, 6)) is False


def test_touching_at_an_endpoint():
    assert segments_intersect((0, 0), (2, 2), (2, 2), (4, 0)) is True
    assert segments_intersect_parametric((0, 0), (2, 2), (2, 2), (4, 0)) is True


def test_collinear_overlapping():
    assert segments_intersect((0, 0), (4, 0), (2, 0), (6, 0)) is True
    assert segments_intersect_parametric((0, 0), (4, 0), (2, 0), (6, 0)) is True


def test_collinear_non_overlapping():
    assert segments_intersect((0, 0), (2, 0), (3, 0), (5, 0)) is False
    assert segments_intersect_parametric((0, 0), (2, 0), (3, 0), (5, 0)) is False


def test_parallel_non_collinear_never_intersect():
    assert segments_intersect((0, 0), (4, 0), (0, 1), (4, 1)) is False
    assert segments_intersect_parametric((0, 0), (4, 0), (0, 1), (4, 1)) is False


def test_one_segment_a_single_point_on_the_other():
    # a degenerate "segment" (both endpoints equal) lying exactly on another segment
    assert segments_intersect((0, 0), (4, 0), (2, 0), (2, 0)) is True


def test_t_junction():
    # one segment's endpoint touches the middle of the other
    assert segments_intersect((0, 0), (4, 0), (2, 0), (2, 3)) is True
    assert segments_intersect_parametric((0, 0), (4, 0), (2, 0), (2, 3)) is True


@pytest.mark.parametrize("seed", range(1000))
def test_orientation_test_matches_parametric_solve_random_segments(seed):
    rng = random.Random(seed)
    p1 = (rng.uniform(-10, 10), rng.uniform(-10, 10))
    p2 = (rng.uniform(-10, 10), rng.uniform(-10, 10))
    p3 = (rng.uniform(-10, 10), rng.uniform(-10, 10))
    p4 = (rng.uniform(-10, 10), rng.uniform(-10, 10))
    a = segments_intersect(p1, p2, p3, p4)
    b = segments_intersect_parametric(p1, p2, p3, p4)
    assert a == b, f"seed={seed}: {p1,p2,p3,p4} orientation={a} parametric={b}"


@pytest.mark.parametrize("seed", range(300))
def test_orientation_test_matches_parametric_solve_integer_grid_segments(seed):
    # small integer coordinates make parallel/collinear/touching-endpoint
    # cases far more likely than continuous random floats would
    rng = random.Random(seed + 4000)
    pts = [(rng.randint(-5, 5), rng.randint(-5, 5)) for _ in range(4)]
    p1, p2, p3, p4 = pts
    a = segments_intersect(p1, p2, p3, p4)
    b = segments_intersect_parametric(p1, p2, p3, p4)
    assert a == b, f"seed={seed}: {pts} orientation={a} parametric={b}"
