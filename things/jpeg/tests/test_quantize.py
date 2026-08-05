import pytest

from jpeg.quantize import (
    CHROMINANCE_BASE, LUMINANCE_BASE, quantize_block, scale_table,
)


def test_quality_50_is_the_identity_base_table():
    assert scale_table(LUMINANCE_BASE, 50) == LUMINANCE_BASE
    assert scale_table(CHROMINANCE_BASE, 50) == CHROMINANCE_BASE


def test_higher_quality_gives_smaller_or_equal_table_entries():
    low = scale_table(LUMINANCE_BASE, 10)
    high = scale_table(LUMINANCE_BASE, 95)
    for row_low, row_high in zip(low, high):
        for a, b in zip(row_low, row_high):
            assert b <= a


def test_table_entries_clamped_to_valid_range():
    for quality in [1, 50, 100]:
        table = scale_table(LUMINANCE_BASE, quality)
        for row in table:
            for value in row:
                assert 1 <= value <= 255


def test_quantize_block_divides_and_rounds():
    coeff = [[16.0] * 8 for _ in range(8)]
    table = [[16] * 8 for _ in range(8)]
    result = quantize_block(coeff, table)
    assert result == [[1] * 8 for _ in range(8)]


def test_quantize_rounds_half_away_from_zero():
    table = [[10] * 8 for _ in range(8)]
    coeff = [[0.0] * 8 for _ in range(8)]
    coeff[0][0] = 5.0   # 5/10 = 0.5 -> rounds to 1
    coeff[0][1] = -5.0  # -0.5 -> rounds to -1
    coeff[0][2] = 4.9   # rounds to 0
    result = quantize_block(coeff, table)
    assert result[0][0] == 1
    assert result[0][1] == -1
    assert result[0][2] == 0


def test_quantize_zero_coefficient_is_zero():
    table = [[16] * 8 for _ in range(8)]
    coeff = [[0.0] * 8 for _ in range(8)]
    result = quantize_block(coeff, table)
    assert all(v == 0 for row in result for v in row)
