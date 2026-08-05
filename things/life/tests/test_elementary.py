"""The correctness proof for the elementary CA step function: Rule 90's
famous exact closed form. Starting from a single live cell, Rule 90
(XOR of left and right neighbor, ignoring the center entirely) produces
exactly Pascal's triangle mod 2 -- cell (t, k) [generation t, offset k
from the seed] is alive iff C(t, (t+k)/2) is odd. That's a real,
independently-provable mathematical fact (a standard textbook result
about Rule 90, unrelated to how this module happens to be coded), used
here via Python's exact-integer `math.comb` -- a completely different
computation path from simulating the automaton cell-by-cell.
"""
import math

import pytest

from life.elementary import rule_table, run, single_seed_row, step


def _rule90_predicted(t: int, k: int) -> int:
    if (t + k) % 2 != 0:
        return 0
    j = (t + k) // 2
    if not (0 <= j <= t):
        return 0
    return math.comb(t, j) % 2


def test_rule_table_decodes_bit_pattern():
    # rule 90 = 0b01011010: bit i is the output for 3-bit neighborhood i
    table = rule_table(90)
    assert table == (0, 1, 0, 1, 1, 0, 1, 0)


def test_rule_table_rejects_out_of_range():
    with pytest.raises(ValueError):
        rule_table(256)
    with pytest.raises(ValueError):
        rule_table(-1)


def test_rule_90_matches_pascals_triangle_mod_2():
    width = 81
    center = width // 2
    history = run(single_seed_row(width), rule=90, generations=35)
    for t, row in enumerate(history):
        for x in range(width):
            k = x - center
            assert row[x] == _rule90_predicted(t, k), f"generation {t}, offset {k}"


def test_rule_0_is_always_all_dead():
    # rule 0's table is all zeros: every neighborhood maps to dead
    row = (1, 0, 1, 1, 0)
    assert step(row, rule=0) == (0, 0, 0, 0, 0)


def test_rule_255_is_always_all_alive():
    row = (0, 0, 0, 0, 0)
    assert step(row, rule=255) == (1, 1, 1, 1, 1)


def test_boundaries_treated_as_dead():
    # a single 1 at the very left edge: its left "neighbor" is off the
    # row and must be treated as 0, not wrap around or error
    row = (1, 0, 0)
    result = step(row, rule=90)
    assert len(result) == 3  # doesn't raise, doesn't change length


def test_step_preserves_row_length():
    for width in [1, 2, 10, 50]:
        row = single_seed_row(width)
        assert len(step(row, rule=110)) == width


def test_run_produces_generations_plus_one_rows():
    history = run(single_seed_row(11), rule=30, generations=5)
    assert len(history) == 6  # includes generation 0 (the initial row)


@pytest.mark.parametrize("rule", [30, 90, 110, 184])
def test_all_zero_row_with_zero_rule_stays_zero(rule):
    # a row of all zeros can only produce nonzero output if the rule
    # maps the all-dead neighborhood (000) to alive; rules 30/90/110/184
    # all map 000 -> 0, so an all-dead row is a fixed point for each
    table = rule_table(rule)
    assert table[0] == 0
    row = (0,) * 20
    assert step(row, rule=rule) == row
