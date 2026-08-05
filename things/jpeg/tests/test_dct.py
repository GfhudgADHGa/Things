"""The DCT's correctness proof: a hand-derived closed form, not a
comparison against another implementation. For a spatially constant
block f(x,y) = c, the definition of the DCT-II gives an exact result --
DC = 8c, every AC coefficient exactly 0 -- because summing cos((2n+1)k*pi/16)
over n=0..7 is zero for every k in 1..7 (this is the same orthogonality
property that makes the DCT basis a basis at all). That's independent of
trusting any particular implementation, JPEG's or otherwise.
"""
import math

import pytest

from jpeg.dct import forward_dct_block

EPS = 1e-9


@pytest.mark.parametrize("c", [0.0, 1.0, -37.5, 127.0, -128.0])
def test_constant_block_has_dc_only(c):
    block = [[c] * 8 for _ in range(8)]
    coeff = forward_dct_block(block)
    assert coeff[0][0] == pytest.approx(8 * c, abs=1e-9)
    for v in range(8):
        for u in range(8):
            if (v, u) != (0, 0):
                assert abs(coeff[v][u]) < EPS


def test_zero_block_is_all_zero():
    coeff = forward_dct_block([[0.0] * 8 for _ in range(8)])
    assert all(abs(coeff[v][u]) < EPS for v in range(8) for u in range(8))


def test_dct_is_linear():
    # DCT is a linear transform: dct(a*x + b*y) == a*dct(x) + b*dct(y)
    import random
    rng = random.Random(0)
    block_x = [[rng.uniform(-50, 50) for _ in range(8)] for _ in range(8)]
    block_y = [[rng.uniform(-50, 50) for _ in range(8)] for _ in range(8)]
    a, b = 2.0, -3.0
    combined = [[a * block_x[i][j] + b * block_y[i][j] for j in range(8)] for i in range(8)]

    dct_x = forward_dct_block(block_x)
    dct_y = forward_dct_block(block_y)
    dct_combined = forward_dct_block(combined)

    for v in range(8):
        for u in range(8):
            expected = a * dct_x[v][u] + b * dct_y[v][u]
            assert dct_combined[v][u] == pytest.approx(expected, abs=1e-6)


def test_parseval_energy_is_exactly_preserved():
    # The 0.5*C(k) normalization used here makes each 1D basis vector
    # unit-norm, so the 2D transform is orthonormal: total energy
    # (sum of squares) is exactly preserved between the spatial block
    # and its DCT coefficients -- another closed-form property, not
    # something read off a reference implementation.
    import random
    rng = random.Random(1)
    block = [[rng.uniform(-128, 127) for _ in range(8)] for _ in range(8)]
    coeff = forward_dct_block(block)
    spatial_energy = sum(v * v for row in block for v in row)
    freq_energy = sum(v * v for row in coeff for v in row)
    assert freq_energy == pytest.approx(spatial_energy, rel=1e-9)
