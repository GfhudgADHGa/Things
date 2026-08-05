"""The correctness proof for grid.step: not comparisons against another
implementation, but exact, well-documented mathematical facts about
specific well-known patterns -- still lifes are exact fixed points,
oscillators return to their exact original state after exactly their
claimed period (and no smaller one), and the glider returns to its
exact original shape, translated by exactly one cell diagonally, after
exactly 4 generations.
"""
import pytest

from life.grid import normalize, step
from life.patterns import GLIDER, GLIDER_PERIOD, OSCILLATORS, STILL_LIFES


@pytest.mark.parametrize("name", sorted(STILL_LIFES))
def test_still_life_is_an_exact_fixed_point(name):
    pattern = STILL_LIFES[name]
    assert step(pattern) == pattern


@pytest.mark.parametrize("name", sorted(STILL_LIFES))
def test_still_life_remains_fixed_over_many_generations(name):
    pattern = STILL_LIFES[name]
    cur = pattern
    for _ in range(20):
        cur = step(cur)
        assert cur == pattern


@pytest.mark.parametrize("name", sorted(OSCILLATORS))
def test_oscillator_returns_after_exactly_its_claimed_period(name):
    pattern, period = OSCILLATORS[name]
    cur = pattern
    for _ in range(period):
        cur = step(cur)
    assert cur == pattern


@pytest.mark.parametrize("name", sorted(OSCILLATORS))
def test_oscillator_does_not_return_before_its_claimed_period(name):
    pattern, period = OSCILLATORS[name]
    cur = pattern
    for i in range(1, period):
        cur = step(cur)
        assert cur != pattern, f"{name} returned to its start state after only {i} steps, not {period}"


@pytest.mark.parametrize("name", sorted(OSCILLATORS))
def test_oscillator_repeats_indefinitely(name):
    pattern, period = OSCILLATORS[name]
    cur = pattern
    for cycle in range(5):
        for _ in range(period):
            cur = step(cur)
        assert cur == pattern


def test_glider_returns_to_its_exact_shape_after_one_period():
    cur = GLIDER
    for _ in range(GLIDER_PERIOD):
        cur = step(cur)
    assert normalize(cur) == normalize(GLIDER)


def test_glider_translates_diagonally_by_exactly_one_cell():
    cur = GLIDER
    for _ in range(GLIDER_PERIOD):
        cur = step(cur)
    dx = min(c[0] for c in cur) - min(c[0] for c in GLIDER)
    dy = min(c[1] for c in cur) - min(c[1] for c in GLIDER)
    assert abs(dx) == 1
    assert abs(dy) == 1


def test_glider_keeps_translating_the_same_way_every_period():
    cur = GLIDER
    positions = []
    for cycle in range(4):
        for _ in range(GLIDER_PERIOD):
            cur = step(cur)
        positions.append((min(c[0] for c in cur), min(c[1] for c in cur)))
    # each successive period should move by the same fixed vector
    deltas = [(positions[i + 1][0] - positions[i][0], positions[i + 1][1] - positions[i][1]) for i in range(3)]
    assert len(set(deltas)) == 1


def test_empty_grid_stays_empty():
    assert step(frozenset()) == frozenset()
