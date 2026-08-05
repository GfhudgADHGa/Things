"""Board representation: an 8x8 array of squares, plus game state, with FEN
import/export. Square index = rank * 8 + file, where rank 0 is rank 1 (white's
back rank) and file 0 is the a-file. A piece is a 2-character string like
"wP" (white pawn) or "bK" (black king); an empty square is None.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, List, Optional

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

FILES = "abcdefgh"
RANKS = "12345678"

_FEN_PIECE_TO_COLOR = {c: ("w" if c.isupper() else "b") for c in "PNBRQKpnbrqk"}


def square_name(square: int) -> str:
    file, rank = square % 8, square // 8
    return f"{FILES[file]}{RANKS[rank]}"


def square_from_name(name: str) -> int:
    file = FILES.index(name[0])
    rank = RANKS.index(name[1])
    return rank * 8 + file


def opposite_color(color: str) -> str:
    return "b" if color == "w" else "w"


@dataclass
class Board:
    squares: List[Optional[str]] = field(default_factory=lambda: [None] * 64)
    to_move: str = "w"
    castling_rights: FrozenSet[str] = frozenset({"K", "Q", "k", "q"})
    en_passant_target: Optional[int] = None
    halfmove_clock: int = 0
    fullmove_number: int = 1

    def copy(self) -> "Board":
        return Board(
            squares=self.squares[:],
            to_move=self.to_move,
            castling_rights=self.castling_rights,
            en_passant_target=self.en_passant_target,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
        )

    def piece_at(self, square: int) -> Optional[str]:
        return self.squares[square]

    def king_square(self, color: str) -> Optional[int]:
        target = color + "K"
        for sq, piece in enumerate(self.squares):
            if piece == target:
                return sq
        return None

    @classmethod
    def from_fen(cls, fen: str) -> "Board":
        parts = fen.strip().split()
        placement, to_move, castling, ep, halfmove, fullmove = parts[:6]

        squares: List[Optional[str]] = [None] * 64
        rank = 7
        file = 0
        for ch in placement:
            if ch == "/":
                rank -= 1
                file = 0
            elif ch.isdigit():
                file += int(ch)
            else:
                color = _FEN_PIECE_TO_COLOR[ch]
                squares[rank * 8 + file] = color + ch.upper()
                file += 1

        castling_rights = frozenset(c for c in castling if c in "KQkq")
        en_passant_target = None if ep == "-" else square_from_name(ep)

        return cls(
            squares=squares,
            to_move=to_move,
            castling_rights=castling_rights,
            en_passant_target=en_passant_target,
            halfmove_clock=int(halfmove),
            fullmove_number=int(fullmove),
        )

    def to_fen(self) -> str:
        rows = []
        for rank in range(7, -1, -1):
            row = ""
            empty_run = 0
            for file in range(8):
                piece = self.squares[rank * 8 + file]
                if piece is None:
                    empty_run += 1
                    continue
                if empty_run:
                    row += str(empty_run)
                    empty_run = 0
                letter = piece[1]
                row += letter if piece[0] == "w" else letter.lower()
            if empty_run:
                row += str(empty_run)
            rows.append(row)
        placement = "/".join(rows)

        castling = "".join(c for c in "KQkq" if c in self.castling_rights) or "-"
        ep = "-" if self.en_passant_target is None else square_name(self.en_passant_target)

        return f"{placement} {self.to_move} {castling} {ep} {self.halfmove_clock} {self.fullmove_number}"

    def __str__(self) -> str:
        lines = []
        for rank in range(7, -1, -1):
            cells = []
            for file in range(8):
                piece = self.squares[rank * 8 + file]
                if piece is None:
                    cells.append(".")
                else:
                    letter = piece[1]
                    cells.append(letter if piece[0] == "w" else letter.lower())
            lines.append(f"{RANKS[rank]} " + " ".join(cells))
        lines.append("  " + " ".join(FILES))
        return "\n".join(lines)
