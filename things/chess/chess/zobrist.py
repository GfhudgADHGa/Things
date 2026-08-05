"""Zobrist hashing: a single 64-bit integer that identifies a position,
built by XOR-ing together random keys for each (piece, square), whose
move it is, castling rights, and the en passant file. Two positions
reached by different move orders (a "transposition") hash identically,
which is exactly what makes a transposition table useful.
"""
from __future__ import annotations

import random

from .board import Board

_PIECES = [color + kind for color in "wb" for kind in "PNBRQK"]
_CASTLING_RIGHTS = ["K", "Q", "k", "q"]

_rng = random.Random(0xC0FFEE)

PIECE_SQUARE_KEYS = {piece: [_rng.getrandbits(64) for _ in range(64)] for piece in _PIECES}
SIDE_TO_MOVE_KEY = _rng.getrandbits(64)
CASTLING_KEYS = {right: _rng.getrandbits(64) for right in _CASTLING_RIGHTS}
EN_PASSANT_FILE_KEYS = [_rng.getrandbits(64) for _ in range(8)]


def zobrist_hash(board: Board) -> int:
    h = 0
    for square, piece in enumerate(board.squares):
        if piece is not None:
            h ^= PIECE_SQUARE_KEYS[piece][square]

    if board.to_move == "b":
        h ^= SIDE_TO_MOVE_KEY

    for right in board.castling_rights:
        h ^= CASTLING_KEYS[right]

    if board.en_passant_target is not None:
        h ^= EN_PASSANT_FILE_KEYS[board.en_passant_target % 8]

    return h
