"""Well-known named Life patterns, each with a documented exact
mathematical property that test_patterns.py checks directly against
`grid.step` -- not "looks plausible when rendered," but "returns to
exactly this frozenset after exactly this many generations."
"""
from __future__ import annotations

# Still lifes: step(pattern) == pattern, exactly, forever.
STILL_LIFES = {
    "block": frozenset({(0, 0), (1, 0), (0, 1), (1, 1)}),
    "beehive": frozenset({(1, 0), (2, 0), (0, 1), (3, 1), (1, 2), (2, 2)}),
    "loaf": frozenset({(1, 0), (2, 0), (0, 1), (3, 1), (1, 2), (3, 2), (2, 3)}),
    "boat": frozenset({(0, 0), (1, 0), (0, 1), (2, 1), (1, 2)}),
    "tub": frozenset({(1, 0), (0, 1), (2, 1), (1, 2)}),
}

# Oscillators: step applied `period` times returns exactly the original
# pattern, and no smaller number of steps does.
OSCILLATORS = {
    "blinker": (frozenset({(0, 0), (1, 0), (2, 0)}), 2),
    "toad": (frozenset({(1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1)}), 2),
    "beacon": (frozenset({(0, 0), (1, 0), (0, 1), (3, 2), (2, 3), (3, 3)}), 2),
}

# The glider: a period-4 oscillator up to translation -- after 4
# generations it's the exact same shape, shifted diagonally by one cell.
GLIDER = frozenset({(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)})
GLIDER_PERIOD = 4
