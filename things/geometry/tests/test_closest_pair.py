import math
import random

import pytest

from geometry.closest_pair import brute_force_closest_pair, closest_pair


def test_two_points():
    pair, dist = closest_pair([(0, 0), (3, 4)])
    assert dist == pytest.approx(5.0)


def test_exact_duplicate_points_give_distance_zero():
    pair, dist = closest_pair([(1, 1), (5, 5), (1, 1)])
    assert dist == 0.0


def test_hand_picked_case():
    pts = [(0, 0), (10, 10), (1, 1), (5, 5)]
    # closest pair is (0,0)-(1,1), distance sqrt(2)
    pair, dist = closest_pair(pts)
    assert dist == pytest.approx(math.sqrt(2))
    assert set(pair) == {(0, 0), (1, 1)}


def test_fewer_than_two_points_raises():
    with pytest.raises(ValueError):
        closest_pair([(0, 0)])


def test_matches_brute_force_on_a_small_hand_case():
    pts = [(0, 0), (1, 0), (0, 1), (5, 5), (5, 6)]
    (p1, d1) = closest_pair(pts)
    (p2, d2) = brute_force_closest_pair(pts)
    assert d1 == pytest.approx(d2)


def _random_points(rng, n, coord_range=100):
    return [(rng.uniform(-coord_range, coord_range), rng.uniform(-coord_range, coord_range)) for _ in range(n)]


@pytest.mark.parametrize("seed", range(300))
def test_matches_brute_force_random_points(seed):
    rng = random.Random(seed)
    n = rng.randint(2, 60)
    pts = _random_points(rng, n)
    (_, d1) = closest_pair(pts)
    (_, d2) = brute_force_closest_pair(pts)
    assert d1 == pytest.approx(d2, abs=1e-9)


@pytest.mark.parametrize("seed", range(50))
def test_matches_brute_force_with_clustered_points(seed):
    # points clustered into a couple of tight groups stress the
    # divide-and-conquer strip logic differently than uniformly
    # scattered points do (many points can fall within the strip at once)
    rng = random.Random(seed + 9000)
    cluster_centers = [(rng.uniform(-50, 50), rng.uniform(-50, 50)) for _ in range(rng.randint(2, 4))]
    pts = []
    for _ in range(rng.randint(10, 60)):
        cx, cy = rng.choice(cluster_centers)
        pts.append((cx + rng.uniform(-1, 1), cy + rng.uniform(-1, 1)))
    (_, d1) = closest_pair(pts)
    (_, d2) = brute_force_closest_pair(pts)
    assert d1 == pytest.approx(d2, abs=1e-9)


@pytest.mark.parametrize("seed", range(30))
def test_matches_brute_force_with_integer_grid_points(seed):
    # a grid produces lots of ties and points exactly on the strip
    # boundary -- a different stress case than continuous random floats
    rng = random.Random(seed + 20000)
    n = rng.randint(2, 40)
    pts = list({(rng.randint(-10, 10), rng.randint(-10, 10)) for _ in range(n)})
    if len(pts) < 2:
        pts.append((0, 0) if pts != [(0, 0)] else (1, 1))
    (_, d1) = closest_pair(pts)
    (_, d2) = brute_force_closest_pair(pts)
    assert d1 == pytest.approx(d2, abs=1e-9)
