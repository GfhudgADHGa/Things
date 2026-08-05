"""The correctness proof for the Mandelbrot escape-time algorithm: not
comparisons against another implementation, but hand-derived closed-form
facts about specific points and about the set's own structure.
"""
import math
import random

import pytest

from fractal.mandelbrot import escape_iterations, in_main_cardioid, in_period2_bulb


def test_origin_never_escapes():
    # z stays exactly 0 forever: z_0=0, z_1=0^2+0=0, ... -- proven bounded
    # regardless of max_iter, not just "didn't escape within N steps."
    for max_iter in [1, 10, 10000]:
        assert escape_iterations(0j, max_iter=max_iter) is None


def test_c_minus_one_has_an_exact_period_2_orbit():
    # z_0=0, z_1=-1, z_2=(-1)^2-1=0, z_3=0^2-1=-1, ... exactly period-2
    # forever -- |z_n| is always 0 or 1, so it can never cross bailout=2,
    # for ANY max_iter. A real escape-time bug (an off-by-one in the
    # iteration formula, a sign error) would very plausibly break this
    # exact periodicity and show up as an eventual "escaped" result.
    for max_iter in [2, 3, 4, 5, 100, 50000]:
        assert escape_iterations(-1 + 0j, max_iter=max_iter) is None


def test_c_one_escapes_at_the_hand_computed_iteration():
    # z_0=0, z_1=1, z_2=2, z_3=5. |z_2|=2 is not > 2 (bailout is a strict
    # inequality), |z_3|=5 > 2 -- escapes after exactly 3 applications of
    # z -> z^2+c, with |z|=5 at the moment of escape. The smooth value is
    # then a fully hand-computable function of that: 3 - log(log(5)/log(2))/log(2)
    # -- not just "some value in a guessed range" (an earlier version of
    # this test assumed the fractional correction always lies in (0, 1),
    # which is false whenever the orbit overshoots the bailout radius by
    # a lot, as it does here; the precise formula is the only thing
    # that's actually guaranteed).
    expected = 3 - math.log(math.log(5.0) / math.log(2.0)) / math.log(2.0)
    result = escape_iterations(1 + 0j, max_iter=100)
    assert result == pytest.approx(expected)


def test_c_two_escapes_immediately():
    # z_0=0, z_1=2 (not > bailout=2, since 2 is not strictly greater than
    # 2), z_2=4+2=6 > 2 -- escapes after exactly 2 applications, |z|=6 at
    # that moment.
    expected = 2 - math.log(math.log(6.0) / math.log(2.0)) / math.log(2.0)
    result = escape_iterations(2 + 0j, max_iter=100)
    assert result == pytest.approx(expected)


def test_far_outside_points_escape_almost_immediately():
    result = escape_iterations(100 + 100j, max_iter=1000)
    assert result is not None
    assert result < 2.0


@pytest.mark.parametrize("seed", range(20))
def test_main_cardioid_points_never_escape(seed):
    # Cross-checks two completely independent derivations of the same
    # fact: the closed-form main-cardioid formula, and brute-force
    # iteration. Points are sampled by construction from inside the
    # cardioid (via its own parametrization) rather than sampled
    # randomly and filtered, so this doesn't depend on in_main_cardioid
    # being correct to find test points -- only to be *consistent* with
    # escape-time.
    rng = random.Random(seed)
    theta = rng.uniform(0, 2 * math.pi)
    radius_fraction = rng.uniform(0, 0.99)  # strictly inside, not on the boundary
    # main cardioid parametrization: c = e^(i*theta)/2 - e^(2i*theta)/4
    boundary = complex(math.cos(theta), math.sin(theta)) / 2 - complex(math.cos(2 * theta), math.sin(2 * theta)) / 4
    c = boundary * radius_fraction  # scaled toward the origin, staying inside
    assert in_main_cardioid(c)
    assert escape_iterations(c, max_iter=5000) is None


@pytest.mark.parametrize("seed", range(20))
def test_period2_bulb_points_never_escape(seed):
    rng = random.Random(seed)
    angle = rng.uniform(0, 2 * math.pi)
    radius = rng.uniform(0, 0.99) * 0.25  # bulb has radius 1/4, centered at -1
    c = complex(-1 + radius * math.cos(angle), radius * math.sin(angle))
    assert in_period2_bulb(c)
    assert escape_iterations(c, max_iter=5000) is None


@pytest.mark.parametrize("seed", range(500))
def test_random_points_in_known_bounded_regions_match_escape_time(seed):
    rng = random.Random(seed + 10000)
    x = rng.uniform(-2.0, 1.0)
    y = rng.uniform(-1.5, 1.5)
    c = complex(x, y)
    if in_main_cardioid(c) or in_period2_bulb(c):
        assert escape_iterations(c, max_iter=3000) is None


@pytest.mark.parametrize("seed", range(300))
def test_conjugate_symmetry(seed):
    # The Mandelbrot set is symmetric about the real axis: conjugating c
    # conjugates the whole orbit at every step (conjugation is a ring
    # homomorphism, so conj(z^2+c) = conj(z)^2+conj(c)), so c and
    # conj(c) must have identical escape behavior -- a structural
    # invariant independent of any specific point's known behavior.
    rng = random.Random(seed)
    c = complex(rng.uniform(-2.0, 1.0), rng.uniform(-1.5, 1.5))
    a = escape_iterations(c, max_iter=300)
    b = escape_iterations(c.conjugate(), max_iter=300)
    assert (a is None) == (b is None)
    if a is not None:
        assert a == pytest.approx(b, abs=1e-9)


def test_bailout_of_exactly_two_is_the_mathematically_minimal_choice():
    # A point with |c| > 2 must have |z_1| = |c| > 2, so it should
    # register as escaped after exactly 1 iteration -- checks that the
    # implementation doesn't require an extra step to "notice."
    result = escape_iterations(3 + 0j, max_iter=10)
    assert result is not None
    assert 0.0 < result <= 1.0


def test_higher_max_iter_never_flips_a_bounded_point_to_escaped():
    # If escape-time reports "bounded" at some max_iter, it must still
    # report "bounded" at any smaller max_iter too (more steps can only
    # ever *discover* an escape that was already going to happen, never
    # invent one) -- checked across a grid of sample points.
    for x in [-1.5, -1.0, -0.5, 0.0, 0.25]:
        for y in [-0.5, 0.0, 0.5]:
            c = complex(x, y)
            small = escape_iterations(c, max_iter=50)
            if small is None:
                assert escape_iterations(c, max_iter=10) is None
