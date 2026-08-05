"""A backtracking solver with constraint propagation: at each step, pick
the empty cell with the fewest remaining candidates (most-constrained-
variable heuristic) and try each one, recursing. Picking the most
constrained cell first makes wrong guesses fail fast, which is what
keeps this fast even on famously hard puzzles.
"""
from __future__ import annotations

from typing import List, Optional

from .board import EMPTY, is_valid_board, peers


def candidates(board: List[int], i: int) -> List[int]:
    if board[i] != EMPTY:
        return []
    used = {board[p] for p in peers(i) if board[p] != EMPTY}
    return [v for v in range(1, 10) if v not in used]


def find_most_constrained_cell(board: List[int]):
    """Returns (index, candidates) for the empty cell with fewest options,
    or (None, None) if the board is full.
    """
    best_index = None
    best_candidates = None
    for i, v in enumerate(board):
        if v != EMPTY:
            continue
        cands = candidates(board, i)
        if best_candidates is None or len(cands) < len(best_candidates):
            best_index, best_candidates = i, cands
            if len(cands) <= 1:
                break  # can't do better than 0 or 1 options
    return best_index, best_candidates


def solve(board: List[int]) -> Optional[List[int]]:
    """Returns a solved copy of the board, or None if unsolvable.

    Checks the given cells for an internal conflict (two peers already
    sharing a value) up front. Without this, a board like that -- e.g. the
    same digit given twice in one row -- isn't detected as broken by the
    backtracking search directly: each individual empty cell's candidate
    list still looks locally fine (excluding a duplicated value just once,
    same as excluding it once normally), so the search can spend a very
    long time exploring an otherwise-plausible-looking but ultimately
    fruitless completion before exhausting every possibility. A cheap
    global validity check catches it instantly instead.
    """
    if not is_valid_board(board):
        return None
    working = board[:]
    if _solve_in_place(working):
        return working
    return None


def _solve_in_place(board: List[int]) -> bool:
    index, cands = find_most_constrained_cell(board)
    if index is None:
        return True  # no empty cells left: solved
    if not cands:
        return False  # empty cell with no legal candidates: dead end

    for value in cands:
        board[index] = value
        if _solve_in_place(board):
            return True
        board[index] = EMPTY
    return False


def count_solutions(board: List[int], limit: int = 2) -> int:
    """Counts solutions, stopping early once `limit` is reached (useful for
    a cheap uniqueness check without fully enumerating a puzzle with many
    solutions).
    """
    if not is_valid_board(board):
        return 0
    working = board[:]
    count = 0

    def search() -> bool:
        nonlocal count
        index, cands = find_most_constrained_cell(working)
        if index is None:
            count += 1
            return count >= limit  # True = stop searching
        if not cands:
            return False

        for value in cands:
            working[index] = value
            if search():
                working[index] = EMPTY
                return True
            working[index] = EMPTY
        return False

    search()
    return count


def has_unique_solution(board: List[int]) -> bool:
    return count_solutions(board, limit=2) == 1
