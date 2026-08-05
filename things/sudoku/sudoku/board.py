"""A Sudoku board: a flat list of 81 cells (row-major), 0 for empty."""
from __future__ import annotations

from typing import List, Optional, Set

SIZE = 9
EMPTY = 0


def row_of(i: int) -> int:
    return i // 9


def col_of(i: int) -> int:
    return i % 9


def box_of(i: int) -> int:
    return (row_of(i) // 3) * 3 + (col_of(i) // 3)


def cell_index(row: int, col: int) -> int:
    return row * 9 + col


_PEERS = None


def peers(i: int) -> Set[int]:
    """All 20 cells sharing a row, column, or 3x3 box with cell i (not including i itself)."""
    global _PEERS
    if _PEERS is None:
        _PEERS = []
        for idx in range(81):
            r, c, b = row_of(idx), col_of(idx), box_of(idx)
            result = {
                j
                for j in range(81)
                if j != idx and (row_of(j) == r or col_of(j) == c or box_of(j) == b)
            }
            _PEERS.append(result)
    return _PEERS[i]


def parse(text: str) -> List[int]:
    """Parses an 81-character puzzle string; '.', '0', or whitespace means empty."""
    cells = [c for c in text if c.isdigit() or c in ".-_"]
    if len(cells) != 81:
        raise ValueError(f"expected 81 cells, got {len(cells)}")
    return [0 if c in ".-_" else int(c) for c in cells]


def to_string(board: List[int]) -> str:
    return "".join(str(v) if v else "." for v in board)


def is_valid_placement(board: List[int], i: int, value: int) -> bool:
    """Would placing `value` at cell i violate row/col/box uniqueness?"""
    return all(board[p] != value for p in peers(i))


def is_complete(board: List[int]) -> bool:
    return all(v != EMPTY for v in board)


def is_valid_board(board: List[int]) -> bool:
    """No duplicate non-zero values in any row, column, or box."""
    groups = []
    for r in range(9):
        groups.append([cell_index(r, c) for c in range(9)])
    for c in range(9):
        groups.append([cell_index(r, c) for r in range(9)])
    for br in range(3):
        for bc in range(3):
            groups.append(
                [cell_index(br * 3 + dr, bc * 3 + dc) for dr in range(3) for dc in range(3)]
            )

    for group in groups:
        values = [board[i] for i in group if board[i] != EMPTY]
        if len(values) != len(set(values)):
            return False
    return True


def pretty(board: List[int]) -> str:
    lines = []
    for r in range(9):
        if r % 3 == 0 and r != 0:
            lines.append("------+-------+------")
        row_cells = []
        for c in range(9):
            if c % 3 == 0 and c != 0:
                row_cells.append("|")
            v = board[cell_index(r, c)]
            row_cells.append(str(v) if v else ".")
        lines.append(" ".join(row_cells))
    return "\n".join(lines)
