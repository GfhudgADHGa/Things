import pytest

from fractal.render import pixel_to_complex, render_julia, render_mandelbrot


def test_pixel_to_complex_center_pixel_is_near_center():
    # the exact center of the grid should map very close to `center`
    # (not bit-exact, since pixel centers vs. the continuous midpoint
    # can be half a pixel off for even dimensions)
    width, height = 100, 100
    c = pixel_to_complex(50, 50, width, height, center=1 + 2j, plane_width=4.0)
    assert abs(c - (1 + 2j)) < 0.05


def test_pixel_to_complex_left_edge_is_left_of_center():
    c_left = pixel_to_complex(0, 50, 100, 100, center=0j, plane_width=4.0)
    c_right = pixel_to_complex(99, 50, 100, 100, center=0j, plane_width=4.0)
    assert c_left.real < 0 < c_right.real


def test_pixel_to_complex_top_is_above_bottom_in_math_convention():
    # image row 0 is the top of the picture, which should map to the
    # *larger* imaginary part (up), since image y grows downward but
    # the complex plane's doesn't
    c_top = pixel_to_complex(50, 0, 100, 100, center=0j, plane_width=4.0)
    c_bottom = pixel_to_complex(50, 99, 100, 100, center=0j, plane_width=4.0)
    assert c_top.imag > c_bottom.imag


def test_pixel_to_complex_respects_aspect_ratio():
    # a non-square image should span proportionally more of one axis
    width, height = 200, 100  # 2:1 aspect ratio
    c_left = pixel_to_complex(0, 50, width, height, center=0j, plane_width=4.0)
    c_top = pixel_to_complex(100, 0, width, height, center=0j, plane_width=4.0)
    assert abs(c_left.real) == pytest.approx(2.0, abs=0.05)  # half of plane_width=4
    assert abs(c_top.imag) == pytest.approx(1.0, abs=0.05)  # half of plane_height=2


def test_render_mandelbrot_produces_correct_dimensions():
    pixels = render_mandelbrot(20, 15, max_iter=50)
    assert len(pixels) == 15
    assert all(len(row) == 20 for row in pixels)


def test_render_mandelbrot_origin_pixel_is_black():
    # center=(0,0) with a small plane_width: the exact center pixel maps
    # very close to c=0, which is deep inside the main cardioid -- must
    # render as black (never-escaped)
    pixels = render_mandelbrot(21, 21, center=0j, plane_width=0.1, max_iter=200)
    assert pixels[10][10] == (0, 0, 0)


def test_render_mandelbrot_far_away_pixel_is_not_black():
    pixels = render_mandelbrot(5, 5, center=100 + 100j, plane_width=1.0, max_iter=200)
    assert pixels[2][2] != (0, 0, 0)


def test_render_julia_produces_correct_dimensions():
    pixels = render_julia(-0.7 + 0.27015j, 20, 15, max_iter=50)
    assert len(pixels) == 15
    assert all(len(row) == 20 for row in pixels)


def test_render_julia_with_c_zero_and_center_zero_is_black_near_origin():
    # c=0, z0 near 0 => |z0| < 1 => orbit shrinks to 0, never escapes
    pixels = render_julia(0j, 21, 21, center=0j, plane_width=0.1, max_iter=200)
    assert pixels[10][10] == (0, 0, 0)


def test_all_pixel_colors_are_valid_rgb_triples():
    pixels = render_mandelbrot(15, 15, max_iter=100)
    for row in pixels:
        for r, g, b in row:
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255
