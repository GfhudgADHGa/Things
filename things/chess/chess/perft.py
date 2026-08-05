"""Perft: counts leaf nodes in the full legal move tree to a given depth.
The standard way to verify a move generator against known-correct counts.
"""
from __future__ import annotations

from .board import Board
from .moves import apply_move, generate_legal_moves


def perft(board: Board, depth: int) -> int:
    if depth == 0:
        return 1
    total = 0
    for move in generate_legal_moves(board):
        total += perft(apply_move(board, move), depth - 1)
    return total
