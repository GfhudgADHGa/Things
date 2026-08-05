"""The whole-pipeline correctness proof: Pillow -- a real, independent
JPEG decoder -- as the oracle. If the markers, quantization tables,
Huffman tables, or entropy-coded bits were wrong in a way that produced
an invalid file, Pillow would refuse to open it (exactly like physics2d's
GIF encoder being checked against Pillow's GIF decoder). Beyond "does it
open," PSNR against the known original image measures how much
information the lossy pipeline actually preserved.
"""
import io
import math
import random

import pytest
from PIL import Image

from jpeg import encode_rgb_image


def _gradient_image(width, height):
    return [
        [((x * 255) // max(width - 1, 1), (y * 255) // max(height - 1, 1), 128) for x in range(width)]
        for y in range(height)
    ]


def _checkerboard_image(width, height, cell=4):
    return [
        [
            (255, 255, 255) if ((x // cell) + (y // cell)) % 2 == 0 else (10, 10, 10)
            for x in range(width)
        ]
        for y in range(height)
    ]


def _random_image(width, height, rng):
    return [[tuple(rng.randint(0, 255) for _ in range(3)) for _ in range(width)] for _ in range(height)]


def _decode_with_pillow(data: bytes):
    im = Image.open(io.BytesIO(data))
    im.load()
    return im.convert("RGB")


def _psnr(original_pixels, decoded_image, width, height):
    se = 0
    for y in range(height):
        for x in range(width):
            r1, g1, b1 = original_pixels[y][x]
            r2, g2, b2 = decoded_image.getpixel((x, y))
            se += (r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2
    mse = se / (width * height * 3)
    if mse == 0:
        return float("inf")
    return 10 * math.log10(255 * 255 / mse)


@pytest.mark.parametrize("width,height", [(64, 48), (16, 16), (8, 8), (13, 7), (1, 1), (33, 65)])
def test_pillow_can_decode_every_size_including_non_multiples_of_8(width, height):
    pixels = _gradient_image(width, height)
    data = encode_rgb_image(pixels, width, height, quality=80)
    decoded = _decode_with_pillow(data)
    assert decoded.size == (width, height)


def test_output_starts_with_soi_and_ends_with_eoi_markers():
    pixels = _gradient_image(16, 16)
    data = encode_rgb_image(pixels, 16, 16, quality=80)
    assert data[:2] == b"\xff\xd8"
    assert data[-2:] == b"\xff\xd9"


def test_solid_color_round_trips_almost_exactly():
    # A constant block's DCT is DC-only (see test_dct.py's closed-form
    # proof), so quantization error should be the *only* source of
    # error -- and even that should be at most a couple of levels.
    width, height = 32, 32
    color = (200, 50, 90)
    pixels = [[color] * width for _ in range(height)]
    data = encode_rgb_image(pixels, width, height, quality=90)
    decoded = _decode_with_pillow(data)
    max_error = max(
        abs(decoded.getpixel((x, y))[c] - color[c])
        for y in range(height)
        for x in range(width)
        for c in range(3)
    )
    assert max_error <= 3


@pytest.mark.parametrize("quality", [5, 25, 50, 75, 95])
def test_psnr_is_reasonable_and_improves_with_quality(quality):
    width, height = 48, 48
    pixels = _gradient_image(width, height)
    data = encode_rgb_image(pixels, width, height, quality=quality)
    decoded = _decode_with_pillow(data)
    psnr = _psnr(pixels, decoded, width, height)
    # even the lowest quality setting shouldn't produce garbage
    assert psnr > 15


def test_psnr_and_file_size_increase_monotonically_with_quality():
    width, height = 48, 48
    pixels = _gradient_image(width, height)
    qualities = [10, 30, 50, 70, 90]
    sizes = []
    psnrs = []
    for q in qualities:
        data = encode_rgb_image(pixels, width, height, quality=q)
        decoded = _decode_with_pillow(data)
        sizes.append(len(data))
        psnrs.append(_psnr(pixels, decoded, width, height))
    assert sizes == sorted(sizes)
    assert psnrs == sorted(psnrs)


def test_checkerboard_high_frequency_content_still_decodes_correctly():
    width, height = 40, 40
    pixels = _checkerboard_image(width, height)
    data = encode_rgb_image(pixels, width, height, quality=90)
    decoded = _decode_with_pillow(data)
    assert decoded.size == (width, height)


@pytest.mark.parametrize("seed", range(20))
def test_fuzz_random_images_of_random_sizes_all_decode(seed):
    rng = random.Random(seed)
    width = rng.randint(1, 50)
    height = rng.randint(1, 50)
    pixels = _random_image(width, height, rng)
    quality = rng.randint(1, 100)
    data = encode_rgb_image(pixels, width, height, quality=quality)
    decoded = _decode_with_pillow(data)
    assert decoded.size == (width, height)


def test_grayscale_looking_image_compresses_well_relative_to_color_noise():
    width, height = 48, 48
    rng = random.Random(2)
    gray_pixels = [[(v, v, v) for v in row] for row in
                   [[rng.randint(0, 255) for _ in range(width)] for _ in range(height)]]
    noisy_pixels = _random_image(width, height, rng)

    gray_data = encode_rgb_image(gray_pixels, width, height, quality=80)
    noisy_data = encode_rgb_image(noisy_pixels, width, height, quality=80)

    # Grayscale content has zero chrominance AC energy (Cb/Cr are
    # constant), so it should compress meaningfully smaller than full
    # RGB noise at the same quality and resolution.
    assert len(gray_data) < len(noisy_data)


def test_invalid_dimensions_raise():
    with pytest.raises(ValueError):
        encode_rgb_image([[(0, 0, 0)]], 0, 1)
    with pytest.raises(ValueError):
        encode_rgb_image([[(0, 0, 0)]], 1, 0)
