"""Conway's Game of Life, and "Life-like" rule variants in general
(configurable birth/survival neighbor counts -- Conway's own rule is
B3/S23: a dead cell with exactly 3 live neighbors is born, a live cell
survives with 2 or 3 live neighbors, everything else dies or stays
dead).

The grid is a sparse set of alive-cell coordinates on an unbounded
plane, not a fixed-size array -- patterns like a glider can wander
forever without ever needing a bounding box.

Two genuinely different code paths compute the same rule, specifically
so a transcription bug in one is unlikely to be replicated in the
other: `step` accumulates neighbor counts in a dict by walking outward
from each alive cell (efficient, and the one actually used for
rendering), while `step_bruteforce` scans every cell in an explicit
padded bounding box and checks each of its 8 neighbor positions
one-by-one via direct set membership. See test_grid.py for the
cross-check across random "soups."
"""
from __future__ import annotations

from typing import FrozenSet, Set, Tuple

Cell = Tuple[int, int]
Cells = FrozenSet[Cell]

CONWAY_BIRTH = frozenset({3})
CONWAY_SURVIVE = frozenset({2, 3})

_NEIGHBOR_OFFSETS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]


def step(cells: Cells, birth: FrozenSet[int] = CONWAY_BIRTH, survive: FrozenSet[int] = CONWAY_SURVIVE) -> Cells:
    neighbor_counts: dict = {}
    for (x, y) in cells:
        for dx, dy in _NEIGHBOR_OFFSETS:
            key = (x + dx, y + dy)
            neighbor_counts[key] = neighbor_counts.get(key, 0) + 1

    next_cells: Set[Cell] = set()
    for cell, count in neighbor_counts.items():
        if cell in cells:
            if count in survive:
                next_cells.add(cell)
        elif count in birth:
            next_cells.add(cell)
    return frozenset(next_cells)


def step_bruteforce(
    cells: Cells, birth: FrozenSet[int] = CONWAY_BIRTH, survive: FrozenSet[int] = CONWAY_SURVIVE
) -> Cells:
    if not cells:
        return frozenset()
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    next_cells: Set[Cell] = set()
    for x in range(min(xs) - 1, max(xs) + 2):
        for y in range(min(ys) - 1, max(ys) + 2):
            count = 0
            for dx, dy in _NEIGHBOR_OFFSETS:
                if (x + dx, y + dy) in cells:
                    count += 1
            alive = (x, y) in cells
            if alive and count in survive:
                next_cells.add((x, y))
            elif not alive and count in birth:
                next_cells.add((x, y))
    return frozenset(next_cells)


def run(cells: Cells, generations: int, birth: FrozenSet[int] = CONWAY_BIRTH, survive: FrozenSet[int] = CONWAY_SURVIVE) -> list:
    history = [cells]
    for _ in range(generations):
        cells = step(cells, birth, survive)
        history.append(cells)
    return history


def normalize(cells: Cells) -> Cells:
    """Translates a pattern so its bounding box's minimum corner is at
    the origin -- lets you compare two occurrences of "the same shape"
    at different positions (e.g. a glider after it has moved)."""
    if not cells:
        return cells
    min_x = min(c[0] for c in cells)
    min_y = min(c[1] for c in cells)
    return frozenset((x - min_x, y - min_y) for x, y in cells)
