"""Cross-checks the two independent step implementations -- `step`
(neighbor-count accumulation) and `step_bruteforce` (explicit bounded
scan checking each of 8 neighbor positions directly) -- against each
other across randomized "soups" and custom Life-like rules, plus
structural properties (Life-like rules only ever change a bounded
region, growth is bounded by the pattern's own extent, etc.).
"""
import random

import pytest

from life.grid import CONWAY_BIRTH, CONWAY_SURVIVE, step, step_bruteforce


def _random_soup(rng, width, height, density=0.35):
    return frozenset(
        (x, y)
        for x in range(width)
        for y in range(height)
        if rng.random() < density
    )


@pytest.mark.parametrize("seed", range(300))
def test_step_matches_bruteforce_random_soups(seed):
    rng = random.Random(seed)
    width = rng.randint(1, 15)
    height = rng.randint(1, 15)
    soup = _random_soup(rng, width, height, density=rng.uniform(0.1, 0.6))
    assert step(soup) == step_bruteforce(soup)


@pytest.mark.parametrize("seed", range(100))
def test_step_matches_bruteforce_over_several_generations(seed):
    rng = random.Random(seed + 1000)
    width = rng.randint(3, 12)
    height = rng.randint(3, 12)
    cells = _random_soup(rng, width, height, density=0.4)
    for _ in range(8):
        a = step(cells)
        b = step_bruteforce(cells)
        assert a == b
        cells = a  # continue evolving via the primary implementation


@pytest.mark.parametrize("rule", [
    (frozenset({3}), frozenset({2, 3})),   # Conway's own B3/S23
    (frozenset({3, 6}), frozenset({2, 3})),  # HighLife B36/S23
    (frozenset({2}), frozenset({}))  ,       # an arbitrary made-up Life-like rule
])
@pytest.mark.parametrize("seed", range(30))
def test_step_matches_bruteforce_for_non_conway_rules(rule, seed):
    birth, survive = rule
    rng = random.Random(seed + 2000)
    soup = _random_soup(rng, rng.randint(3, 10), rng.randint(3, 10), density=0.4)
    assert step(soup, birth, survive) == step_bruteforce(soup, birth, survive)


def test_empty_grid_stays_empty_both_implementations():
    assert step(frozenset()) == frozenset()
    assert step_bruteforce(frozenset()) == frozenset()


def test_single_cell_dies_of_isolation():
    assert step(frozenset({(0, 0)})) == frozenset()


def test_default_rule_is_conway():
    assert CONWAY_BIRTH == frozenset({3})
    assert CONWAY_SURVIVE == frozenset({2, 3})


@pytest.mark.parametrize("seed", range(50))
def test_pattern_never_grows_beyond_one_cell_of_its_bounding_box(seed):
    # a single generation of Life-like rules can only ever create new
    # alive cells adjacent to a previously-alive cell -- so the new
    # pattern's bounding box can grow by at most 1 in every direction
    rng = random.Random(seed + 3000)
    soup = _random_soup(rng, rng.randint(3, 10), rng.randint(3, 10), density=0.4)
    if not soup:
        return
    next_gen = step(soup)
    if not next_gen:
        return
    old_xs, old_ys = [c[0] for c in soup], [c[1] for c in soup]
    new_xs, new_ys = [c[0] for c in next_gen], [c[1] for c in next_gen]
    assert min(new_xs) >= min(old_xs) - 1
    assert max(new_xs) <= max(old_xs) + 1
    assert min(new_ys) >= min(old_ys) - 1
    assert max(new_ys) <= max(old_ys) + 1
