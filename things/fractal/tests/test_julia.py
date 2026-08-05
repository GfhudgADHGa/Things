import random

import pytest

from fractal.julia import escape_iterations


def test_z0_zero_c_zero_never_escapes():
    # z stays exactly 0 forever
    assert escape_iterations(0j, 0j, max_iter=10000) is None


def test_far_starting_point_escapes_almost_immediately():
    result = escape_iterations(100 + 100j, 0.3 + 0.5j, max_iter=1000)
    assert result is not None
    assert result < 2.0


def test_hand_computed_orbit_c_zero():
    # With c=0, z_{n+1} = z_n^2, so |z_n| = |z_0|^n. Starting from
    # z_0=1.5 (|z_0|=1.5 > 1, so it grows): |z_1|=2.25 > bailout=2 --
    # escapes after exactly 1 application.
    result = escape_iterations(1.5 + 0j, 0j, max_iter=100)
    assert result is not None
    assert 0.0 < result <= 1.0


def test_z0_on_unit_circle_with_c_zero_stays_bounded_for_a_while():
    # In *exact* arithmetic, |z_0|=1 implies |z_n|=1 for all n (z->z^2
    # preserves modulus exactly), so this should never escape for any
    # max_iter. It doesn't hold in floating point past roughly 50
    # iterations: z->z^2 with c=0 is exactly the angle-doubling map
    # (z_n = e^{i*2^n*theta}), a textbook chaotic system, and doubling a
    # value each step means a relative floating-point rounding error of
    # size epsilon roughly *doubles* every iteration too (squaring
    # (1+eps) gives 1+2*eps to first order). Starting from double
    # precision's ~2^-52 epsilon, 2^n * 2^-52 ~ O(1) right around
    # n ~ 52 -- which is exactly where this stops holding numerically
    # (empirically, some angles escape by n=54). That's the real
    # dynamical system being genuinely chaotic, not a bug in
    # escape_iterations -- the original version of this test asserted
    # "never escapes" up to max_iter=5000 and failed for exactly this
    # reason, so the bound here is chosen well inside the region where
    # floating-point precision can still track the true orbit.
    import math
    for angle in [0.0, 1.0, 2.5, 4.1, 6.0]:
        z0 = complex(math.cos(angle), math.sin(angle))
        assert escape_iterations(z0, 0j, max_iter=35) is None


@pytest.mark.parametrize("seed", range(300))
def test_conjugate_symmetry_when_c_is_real(seed):
    # z -> z^2 + c commutes with conjugation for any c, but when c is
    # real, conj(c) == c, so conjugating *only* z_0 still conjugates the
    # entire orbit at every step -- meaning escape behavior for z_0 and
    # conj(z_0) must match whenever c itself is real.
    rng = random.Random(seed)
    z0 = complex(rng.uniform(-2, 2), rng.uniform(-2, 2))
    c = complex(rng.uniform(-1.5, 1.5), 0.0)
    a = escape_iterations(z0, c, max_iter=300)
    b = escape_iterations(z0.conjugate(), c, max_iter=300)
    assert (a is None) == (b is None)
    if a is not None:
        assert a == pytest.approx(b, abs=1e-9)


def test_higher_max_iter_never_flips_bounded_to_escaped():
    z0, c = 0.1 + 0.1j, -0.7 + 0.27015j
    small = escape_iterations(z0, c, max_iter=20)
    if small is None:
        assert escape_iterations(z0, c, max_iter=5) is None
