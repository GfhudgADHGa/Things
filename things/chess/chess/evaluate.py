"""Static position evaluation: material + simple piece-square tables.

Returns a score in centipawns from White's perspective (positive = better
for White). This is a deliberately simple, hand-tuned evaluation -- no
tablebases, no learned weights -- good enough to give the search something
sensible to optimize.
"""
from __future__ import annotations

from .board import Board

PIECE_VALUES = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}

# Indexed [rank][file], rank 0 = rank 1 (White's back rank). Encourages
# central control and pawn advancement; mirrored vertically for Black.
_PAWN_PST = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 10, 10, -10, -10, 10, 10, 5],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

_KNIGHT_PST = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]

_CENTER_PST = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]

_KING_PST = [
    [20, 30, 10, 0, 0, 10, 30, 20],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
]

_PST = {"P": _PAWN_PST, "N": _KNIGHT_PST, "B": _CENTER_PST, "R": _CENTER_PST, "Q": _CENTER_PST, "K": _KING_PST}


def evaluate(board: Board) -> float:
    score = 0.0
    for sq, piece in enumerate(board.squares):
        if piece is None:
            continue
        color, kind = piece[0], piece[1]
        file, rank = sq % 8, sq // 8
        value = PIECE_VALUES[kind]
        pst_rank = rank if color == "w" else 7 - rank
        positional = _PST[kind][pst_rank][file]
        score += (value + positional) if color == "w" else -(value + positional)
    return score
