"""Wolfram's elementary cellular automata: a 1D row of cells, each
generation computed from the previous one by looking at each cell's
3-cell neighborhood (left, center, right) and looking up the result in
an 8-entry rule table -- 256 possible rules total (2^8 possible tables),
numbered by treating the table as an 8-bit binary number (Wolfram's own
numbering convention: bit i of the rule number is the output for the
neighborhood pattern encoding integer i).

Rule 110 is famously Turing-complete. Rule 90 has an exact closed-form
description used as a correctness proof in test_elementary.py: starting
from a single live cell, it produces exactly Pascal's triangle mod 2
(the Sierpinski triangle) -- a well-known, independently provable
mathematical fact that has nothing to do with simulating the automaton,
which is exactly what makes it a real cross-check rather than a
restatement of the implementation.
"""
from __future__ import annotations

from typing import Tuple

Row = Tuple[int, ...]


def rule_table(rule: int) -> Tuple[int, ...]:
    if not 0 <= rule <= 255:
        raise ValueError("rule must be between 0 and 255")
    return tuple((rule >> i) & 1 for i in range(8))


def step(row: Row, rule: int) -> Row:
    table = rule_table(rule)
    n = len(row)
    next_row = []
    for i in range(n):
        left = row[i - 1] if i > 0 else 0
        center = row[i]
        right = row[i + 1] if i < n - 1 else 0
        pattern = (left << 2) | (center << 1) | right
        next_row.append(table[pattern])
    return tuple(next_row)


def run(row: Row, rule: int, generations: int) -> list:
    history = [row]
    for _ in range(generations):
        row = step(row, rule)
        history.append(row)
    return history


def single_seed_row(width: int) -> Row:
    """A row of the given width, all zero except a single 1 at the
    center -- the standard starting condition used to visualize (and
    here, to verify) elementary CA rules."""
    row = [0] * width
    row[width // 2] = 1
    return tuple(row)
