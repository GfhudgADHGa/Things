import colorsys
import random

import pytest

from fractal.color import hsv_to_rgb, smooth_color


@pytest.mark.parametrize("seed", range(500))
def test_hsv_to_rgb_matches_colorsys_oracle(seed):
    rng = random.Random(seed)
    h, s, v = rng.random(), rng.random(), rng.random()
    mine = hsv_to_rgb(h, s, v)
    reference = colorsys.hsv_to_rgb(h, s, v)
    for a, b in zip(mine, reference):
        assert a == pytest.approx(b, abs=1e-9)


def test_hsv_to_rgb_known_pure_colors():
    assert hsv_to_rgb(0.0, 1.0, 1.0) == pytest.approx((1.0, 0.0, 0.0))  # red
    r, g, b = hsv_to_rgb(1 / 3, 1.0, 1.0)
    assert (r, round(g), b) == pytest.approx((0.0, 1.0, 0.0), abs=1e-9)  # green
    r, g, b = hsv_to_rgb(2 / 3, 1.0, 1.0)
    assert (round(r), g, b) == pytest.approx((0.0, 0.0, 1.0), abs=1e-9)  # blue


def test_hsv_to_rgb_zero_saturation_is_grayscale():
    r, g, b = hsv_to_rgb(0.37, 0.0, 0.6)
    assert r == pytest.approx(0.6)
    assert g == pytest.approx(0.6)
    assert b == pytest.approx(0.6)


def test_hsv_to_rgb_hue_wraps_around():
    assert hsv_to_rgb(0.0, 0.5, 0.5) == pytest.approx(hsv_to_rgb(1.0, 0.5, 0.5))
    assert hsv_to_rgb(0.2, 0.5, 0.5) == pytest.approx(hsv_to_rgb(1.2, 0.5, 0.5))


def test_smooth_color_of_none_is_black():
    assert smooth_color(None) == (0, 0, 0)


def test_smooth_color_returns_valid_rgb_bytes():
    for iterations in [0.0, 1.5, 100.0, 9999.9]:
        r, g, b = smooth_color(iterations)
        assert 0 <= r <= 255
        assert 0 <= g <= 255
        assert 0 <= b <= 255


def test_smooth_color_cycles():
    # exactly one full cycle apart should give (essentially) the same color
    a = smooth_color(5.0, cycle=32.0)
    b = smooth_color(5.0 + 32.0, cycle=32.0)
    assert a == b
