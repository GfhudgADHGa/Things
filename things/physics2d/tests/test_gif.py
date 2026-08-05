"""Correctness oracle: decode our own GIF output with Pillow (a real,
independent GIF decoder) and check the pixels come back exactly right.
Trusting our own hand-rolled LZW decoder would prove nothing -- if the
encoder and a from-scratch decoder shared the same bug, they'd agree with
each other and still be wrong. Pillow has no knowledge of how our encoder
works, so agreement with it is real evidence of correctness.
"""
import random

import pytest
from PIL import Image

from physics2d.gif import _lzw_encode, encode_gif


def _make_frame(width, height, fill):
    return [[fill for _ in range(width)] for _ in range(height)]


def test_single_solid_frame_roundtrips(tmp_path):
    path = str(tmp_path / "test.gif")
    frame = _make_frame(5, 5, (200, 50, 50))
    encode_gif([frame], path)

    img = Image.open(path).convert("RGB")
    assert img.size == (5, 5)
    for y in range(5):
        for x in range(5):
            assert img.getpixel((x, y)) == (200, 50, 50)


def test_two_color_frame_roundtrips(tmp_path):
    path = str(tmp_path / "test.gif")
    frame = [[(255, 0, 0) if (x + y) % 2 == 0 else (0, 0, 255) for x in range(6)] for y in range(6)]
    encode_gif([frame], path)

    img = Image.open(path).convert("RGB")
    for y in range(6):
        for x in range(6):
            expected = (255, 0, 0) if (x + y) % 2 == 0 else (0, 0, 255)
            assert img.getpixel((x, y)) == expected


def test_multi_frame_animation_roundtrips(tmp_path):
    path = str(tmp_path / "test.gif")
    frames = [_make_frame(4, 4, color) for color in [(255, 0, 0), (0, 255, 0), (0, 0, 255)]]
    encode_gif(frames, path)

    img = Image.open(path)
    assert img.n_frames == 3
    for i, expected_color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]):
        img.seek(i)
        rgb = img.convert("RGB")
        assert rgb.getpixel((0, 0)) == expected_color


def test_random_noise_image_roundtrips_exactly(tmp_path):
    """Stresses LZW code-width growth across many levels."""
    random.seed(42)
    width, height = 40, 30
    palette = [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for _ in range(64)]
    frame = [[random.choice(palette) for _ in range(width)] for _ in range(height)]

    path = str(tmp_path / "test.gif")
    encode_gif([frame], path)

    img = Image.open(path).convert("RGB")
    for y in range(height):
        for x in range(width):
            assert img.getpixel((x, y)) == frame[y][x]


def test_large_palette_forces_table_reset_and_still_roundtrips(tmp_path):
    """Enough distinct colors + enough pixels to exhaust the 12-bit LZW
    table at least once, forcing a mid-stream Clear code."""
    random.seed(7)
    width, height = 80, 80
    palette = [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for _ in range(200)]
    frame = [[random.choice(palette) for _ in range(width)] for _ in range(height)]

    path = str(tmp_path / "test.gif")
    encode_gif([frame], path)

    img = Image.open(path).convert("RGB")
    mismatches = sum(
        1 for y in range(height) for x in range(width) if img.getpixel((x, y)) != frame[y][x]
    )
    assert mismatches == 0


def test_too_many_colors_raises(tmp_path):
    frame = [[(r, 0, 0) for r in range(257)]]
    with pytest.raises(ValueError):
        encode_gif([frame], str(tmp_path / "test.gif"))


def test_empty_frames_list_raises(tmp_path):
    with pytest.raises(ValueError):
        encode_gif([], str(tmp_path / "test.gif"))


def test_lzw_encode_empty_indices_is_just_clear_and_end():
    data = _lzw_encode([], min_code_size=2)
    assert len(data) > 0  # at minimum encodes clear+end codes


def test_lzw_encode_single_pixel():
    data = _lzw_encode([0], min_code_size=2)
    assert len(data) > 0


def test_gif_file_starts_with_correct_header(tmp_path):
    path = str(tmp_path / "test.gif")
    encode_gif([_make_frame(2, 2, (0, 0, 0))], path)
    with open(path, "rb") as f:
        header = f.read(6)
    assert header == b"GIF89a"


def test_gif_ends_with_trailer_byte(tmp_path):
    path = str(tmp_path / "test.gif")
    encode_gif([_make_frame(2, 2, (0, 0, 0))], path)
    with open(path, "rb") as f:
        data = f.read()
    assert data[-1] == 0x3B
