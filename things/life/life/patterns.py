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

# The Gosper glider gun: the first pattern ever found with unbounded
# population growth. Its 36-cell "gun" oscillates with period 30 and
# emits one new glider every cycle, forever -- test_glider_gun.py
# checks the exact closed-form consequence of that: total population
# after 30*k generations equals 36 + 5*k for every k, since each
# emitted glider (5 cells) survives and moves off indefinitely while
# the gun itself returns to an equivalent state every 30 steps.
GOSPER_GLIDER_GUN = frozenset({
    (24, 0),
    (22, 1), (24, 1),
    (12, 2), (13, 2), (20, 2), (21, 2), (34, 2), (35, 2),
    (11, 3), (15, 3), (20, 3), (21, 3), (34, 3), (35, 3),
    (0, 4), (1, 4), (10, 4), (16, 4), (20, 4), (21, 4),
    (0, 5), (1, 5), (10, 5), (14, 5), (16, 5), (17, 5), (22, 5), (24, 5),
    (10, 6), (16, 6), (24, 6),
    (11, 7), (15, 7),
    (12, 8), (13, 8),
})
GLIDER_GUN_PERIOD = 30
