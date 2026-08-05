"""The Gosper glider gun: proof by an exact closed-form population
count, plus a direct structural check that the extra cells really are
gliders and not just an unexplained pile of live cells."""
from __future__ import annotations

import pytest

from life.grid import CONWAY_BIRTH, CONWAY_SURVIVE, normalize, step
from life.patterns import GLIDER, GLIDER_GUN_PERIOD, GLIDER_PERIOD, GOSPER_GLIDER_GUN

_NEIGHBOR_OFFSETS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]


def _connected_components(cells):
    remaining = set(cells)
    components = []
    while remaining:
        start = next(iter(remaining))
        stack = [start]
        remaining.discard(start)
        component = {start}
        while stack:
            x, y = stack.pop()
            for dx, dy in _NEIGHBOR_OFFSETS:
                neighbor = (x + dx, y + dy)
                if neighbor in remaining:
                    remaining.discard(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(frozenset(component))
    return components


def _canonical_glider_shapes():
    """The glider's 4 phases, each normalized to its own bounding box --
    used to recognize a glider regardless of which of the 4 phases of
    its cycle it happens to be in when we sample the gun."""
    shapes = set()
    cells = GLIDER
    for _ in range(GLIDER_PERIOD):
        shapes.add(normalize(cells))
        cells = step(cells, CONWAY_BIRTH, CONWAY_SURVIVE)
    return shapes


CANONICAL_GLIDER_SHAPES = _canonical_glider_shapes()


def test_canonical_glider_has_four_distinct_phases():
    assert len(CANONICAL_GLIDER_SHAPES) == 4


@pytest.mark.parametrize("k", range(1, 21))
def test_population_matches_exact_closed_form(k):
    """population(30*k) == 36 + 5*k: the 36-cell gun returns to an
    equivalent state every 30 generations, and every cycle leaves
    behind exactly one more surviving 5-cell glider than the cycle
    before, so total population grows by exactly 5 every 30 steps."""
    cells = GOSPER_GLIDER_GUN
    for _ in range(GLIDER_GUN_PERIOD * k):
        cells = step(cells, CONWAY_BIRTH, CONWAY_SURVIVE)
    assert len(cells) == 36 + 5 * k


def test_population_fluctuates_within_a_cycle_but_not_across_cycles():
    """Population is *not* monotonic generation-by-generation -- the
    gun's own internal machinery (a queen-bee-shuttle-like oscillator)
    dips and recovers within each 30-step cycle before a new glider
    fully separates. What's actually true, and checked here, is the
    weaker and correct claim: sampled once per full cycle, at every
    multiple of 30 generations, population strictly increases."""
    cells = GOSPER_GLIDER_GUN
    per_generation = [len(cells)]
    for _ in range(60):
        cells = step(cells, CONWAY_BIRTH, CONWAY_SURVIVE)
        per_generation.append(len(cells))
    assert any(per_generation[i + 1] < per_generation[i] for i in range(len(per_generation) - 1))

    checkpoints = [per_generation[g] for g in (0, 30, 60)]
    assert checkpoints == sorted(checkpoints)
    assert checkpoints[1] > checkpoints[0]
    assert checkpoints[2] > checkpoints[1]


def test_extra_cells_are_actually_gliders():
    """Structural check, not just a cell-count coincidence: by
    generation 300 (10 emission cycles in), extract every connected
    5-cell component and confirm each one's shape -- normalized to its
    own bounding box -- matches one of the glider's 4 canonical phases."""
    cells = GOSPER_GLIDER_GUN
    for _ in range(300):
        cells = step(cells, CONWAY_BIRTH, CONWAY_SURVIVE)

    components = _connected_components(cells)
    five_cell_components = [c for c in components if len(c) == 5]
    assert len(five_cell_components) >= 9  # 10 cycles elapsed, gun itself isn't a 5-cell component

    for component in five_cell_components:
        assert normalize(component) in CANONICAL_GLIDER_SHAPES


def test_gun_alone_eventually_returns_close_to_its_start_plus_launched_gliders():
    """A weaker, independent sanity check on the period claim: the
    total *count* of 5-cell (glider-shaped) components found present at
    generation 30*k should itself grow by exactly 1 each cycle, once
    the first glider has had time to fully separate from the gun body."""
    cells = GOSPER_GLIDER_GUN
    counts = []
    for k in range(1, 11):
        for _ in range(GLIDER_GUN_PERIOD):
            cells = step(cells, CONWAY_BIRTH, CONWAY_SURVIVE)
        components = _connected_components(cells)
        five_cell = sum(1 for c in components if len(c) == 5 and normalize(c) in CANONICAL_GLIDER_SHAPES)
        counts.append(five_cell)

    # skip the first couple of cycles: the newest glider or two may
    # still be touching/adjacent to the gun body and not yet count as
    # its own isolated component
    stable = counts[3:]
    diffs = [stable[i + 1] - stable[i] for i in range(len(stable) - 1)]
    assert all(d == 1 for d in diffs), counts
