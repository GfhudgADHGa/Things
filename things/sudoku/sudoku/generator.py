"""Generates puzzles: fill a random valid grid, then remove givens one at
a time (in random order), keeping a removal only if the puzzle still has
exactly one solution.
"""
from __future__ import annotations

import random
from typing import List, Optional

from .board import EMPTY
from .solver import candidates, count_solutions, find_most_constrained_cell


def generate_solved_grid(rng: Optional[random.Random] = None) -> List[int]:
    rng = rng or random.Random()
    board = [EMPTY] * 81

    def backtrack() -> bool:
        index, cands = find_most_constrained_cell(board)
        if index is None:
            return True
        if not cands:
            return False
        shuffled = cands[:]
        rng.shuffle(shuffled)
        for value in shuffled:
            board[index] = value
            if backtrack():
                return True
            board[index] = EMPTY
        return False

    backtrack()
    return board


def generate_puzzle(seed: Optional[int] = None, min_clues: int = 24) -> List[int]:
    """Returns a puzzle (many cells set to 0) with exactly one solution.

    Removes cells greedily until either every cell has been tried or the
    puzzle has been pared down to `min_clues` givens, whichever comes
    first -- puzzles with very few givens take much longer to verify as
    unique, so `min_clues` bounds the generation time.
    """
    rng = random.Random(seed)
    board = generate_solved_grid(rng)
    puzzle = board[:]

    order = list(range(81))
    rng.shuffle(order)

    clues_remaining = 81
    for index in order:
        if clues_remaining <= min_clues:
            break
        if puzzle[index] == EMPTY:
            continue

        saved = puzzle[index]
        puzzle[index] = EMPTY
        if count_solutions(puzzle, limit=2) == 1:
            clues_remaining -= 1
        else:
            puzzle[index] = saved

    return puzzle


def rate_difficulty(puzzle: List[int]) -> str:
    """A simple technique-based rating: how far can pure logical
    elimination (no guessing) get before it needs to backtrack?
    """
    remaining = _solve_by_elimination_only(puzzle)
    empty_count = sum(1 for v in remaining if v == EMPTY)

    if empty_count == 0:
        return "easy"
    if empty_count <= 8:
        return "medium"
    return "hard"


def _solve_by_elimination_only(puzzle: List[int]) -> List[int]:
    """Repeatedly fills in any cell with exactly one candidate (a "naked
    single") until no more progress can be made without guessing. Returns
    the board in whatever state that leaves it -- fully solved for an easy
    puzzle, partially filled for anything that needs real search.
    """
    board = puzzle[:]
    while True:
        progress = False
        for i, v in enumerate(board):
            if v != EMPTY:
                continue
            cands = candidates(board, i)
            if len(cands) == 1:
                board[i] = cands[0]
                progress = True
        if not progress:
            return board
