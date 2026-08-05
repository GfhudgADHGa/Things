"""Legal move generation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .board import Board, opposite_color, square_name

BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS
KNIGHT_OFFSETS = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]

PROMOTION_PIECES = ("Q", "R", "B", "N")


@dataclass(frozen=True)
class Move:
    from_sq: int
    to_sq: int
    promotion: Optional[str] = None
    is_en_passant: bool = False
    is_castle_kingside: bool = False
    is_castle_queenside: bool = False

    def to_uci(self) -> str:
        promo = self.promotion.lower() if self.promotion else ""
        return square_name(self.from_sq) + square_name(self.to_sq) + promo


# (right, king_from, king_to, rook_from, rook_to, must_be_empty, king_path)
_CASTLING = {
    ("w", "K"): (4, 6, 7, 5, [5, 6], [4, 5, 6]),
    ("w", "Q"): (4, 2, 0, 3, [1, 2, 3], [4, 3, 2]),
    ("b", "k"): (60, 62, 63, 61, [61, 62], [60, 61, 62]),
    ("b", "q"): (60, 58, 56, 59, [57, 58, 59], [60, 59, 58]),
}


def _in_bounds(file: int, rank: int) -> bool:
    return 0 <= file < 8 and 0 <= rank < 8


def is_square_attacked(board: Board, square: int, by_color: str) -> bool:
    target_file, target_rank = square % 8, square // 8

    # pawns
    pawn_rank_offset = -1 if by_color == "w" else 1  # attacker's pawn sits one rank "behind"
    for df in (-1, 1):
        f, r = target_file + df, target_rank + pawn_rank_offset
        if _in_bounds(f, r) and board.squares[r * 8 + f] == by_color + "P":
            return True

    # knights
    for df, dr in KNIGHT_OFFSETS:
        f, r = target_file + df, target_rank + dr
        if _in_bounds(f, r) and board.squares[r * 8 + f] == by_color + "N":
            return True

    # king
    for df in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if df == 0 and dr == 0:
                continue
            f, r = target_file + df, target_rank + dr
            if _in_bounds(f, r) and board.squares[r * 8 + f] == by_color + "K":
                return True

    # sliding pieces
    for dirs, kinds in ((BISHOP_DIRS, ("B", "Q")), (ROOK_DIRS, ("R", "Q"))):
        for df, dr in dirs:
            f, r = target_file + df, target_rank + dr
            while _in_bounds(f, r):
                piece = board.squares[r * 8 + f]
                if piece is not None:
                    if piece[0] == by_color and piece[1] in kinds:
                        return True
                    break
                f += df
                r += dr

    return False


def is_in_check(board: Board, color: str) -> bool:
    king_sq = board.king_square(color)
    if king_sq is None:
        return False
    return is_square_attacked(board, king_sq, opposite_color(color))


def _pseudo_pawn_moves(board: Board, sq: int, color: str) -> List[Move]:
    moves = []
    file, rank = sq % 8, sq // 8
    direction = 1 if color == "w" else -1
    start_rank = 1 if color == "w" else 6
    promo_rank = 7 if color == "w" else 0

    def add(to_sq, is_ep=False):
        to_rank = to_sq // 8
        if to_rank == promo_rank:
            for p in PROMOTION_PIECES:
                moves.append(Move(sq, to_sq, promotion=p))
        else:
            moves.append(Move(sq, to_sq, is_en_passant=is_ep))

    one_step_rank = rank + direction
    if _in_bounds(file, one_step_rank):
        one_sq = one_step_rank * 8 + file
        if board.squares[one_sq] is None:
            add(one_sq)
            two_step_rank = rank + 2 * direction
            if rank == start_rank and _in_bounds(file, two_step_rank):
                two_sq = two_step_rank * 8 + file
                if board.squares[two_sq] is None:
                    moves.append(Move(sq, two_sq))

    for df in (-1, 1):
        cf, cr = file + df, rank + direction
        if not _in_bounds(cf, cr):
            continue
        target = cr * 8 + cf
        piece = board.squares[target]
        if piece is not None and piece[0] != color:
            add(target)
        elif board.en_passant_target == target:
            add(target, is_ep=True)

    return moves


def _pseudo_knight_moves(board: Board, sq: int, color: str) -> List[Move]:
    moves = []
    file, rank = sq % 8, sq // 8
    for df, dr in KNIGHT_OFFSETS:
        f, r = file + df, rank + dr
        if not _in_bounds(f, r):
            continue
        target = r * 8 + f
        piece = board.squares[target]
        if piece is None or piece[0] != color:
            moves.append(Move(sq, target))
    return moves


def _pseudo_sliding_moves(board: Board, sq: int, color: str, dirs) -> List[Move]:
    moves = []
    file, rank = sq % 8, sq // 8
    for df, dr in dirs:
        f, r = file + df, rank + dr
        while _in_bounds(f, r):
            target = r * 8 + f
            piece = board.squares[target]
            if piece is None:
                moves.append(Move(sq, target))
            else:
                if piece[0] != color:
                    moves.append(Move(sq, target))
                break
            f += df
            r += dr
    return moves


def _pseudo_king_moves(board: Board, sq: int, color: str) -> List[Move]:
    moves = []
    file, rank = sq % 8, sq // 8
    for df in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if df == 0 and dr == 0:
                continue
            f, r = file + df, rank + dr
            if not _in_bounds(f, r):
                continue
            target = r * 8 + f
            piece = board.squares[target]
            if piece is None or piece[0] != color:
                moves.append(Move(sq, target))

    opponent = opposite_color(color)
    for right in ("K", "Q") if color == "w" else ("k", "q"):
        if right not in board.castling_rights:
            continue
        _, king_to, _, _, must_be_empty, king_path = _CASTLING[(color, right)]
        if any(board.squares[s] is not None for s in must_be_empty):
            continue
        if any(is_square_attacked(board, s, opponent) for s in king_path):
            continue
        is_kingside = right in ("K", "k")
        moves.append(
            Move(
                sq,
                king_to,
                is_castle_kingside=is_kingside,
                is_castle_queenside=not is_kingside,
            )
        )
    return moves


def generate_pseudo_legal_moves(board: Board) -> List[Move]:
    color = board.to_move
    moves: List[Move] = []
    for sq, piece in enumerate(board.squares):
        if piece is None or piece[0] != color:
            continue
        kind = piece[1]
        if kind == "P":
            moves.extend(_pseudo_pawn_moves(board, sq, color))
        elif kind == "N":
            moves.extend(_pseudo_knight_moves(board, sq, color))
        elif kind == "B":
            moves.extend(_pseudo_sliding_moves(board, sq, color, BISHOP_DIRS))
        elif kind == "R":
            moves.extend(_pseudo_sliding_moves(board, sq, color, ROOK_DIRS))
        elif kind == "Q":
            moves.extend(_pseudo_sliding_moves(board, sq, color, QUEEN_DIRS))
        elif kind == "K":
            moves.extend(_pseudo_king_moves(board, sq, color))
    return moves


def apply_move(board: Board, move: Move) -> Board:
    new = board.copy()
    color = board.to_move
    opponent = opposite_color(color)
    piece = new.squares[move.from_sq]
    assert piece is not None, "no piece on from_sq"

    new.en_passant_target = None

    if move.is_en_passant:
        captured_sq = move.to_sq - 8 if color == "w" else move.to_sq + 8
        new.squares[captured_sq] = None

    is_capture = new.squares[move.to_sq] is not None
    is_pawn_move = piece[1] == "P"

    new.squares[move.to_sq] = piece
    new.squares[move.from_sq] = None

    if move.promotion:
        new.squares[move.to_sq] = color + move.promotion

    if move.is_castle_kingside or move.is_castle_queenside:
        right = "K" if move.is_castle_kingside else "Q"
        if color == "b":
            right = right.lower()
        _, _, rook_from, rook_to, _, _ = _CASTLING[(color, right)]
        new.squares[rook_to] = new.squares[rook_from]
        new.squares[rook_from] = None

    if is_pawn_move and abs(move.to_sq - move.from_sq) == 16:
        new.en_passant_target = (move.from_sq + move.to_sq) // 2

    # castling rights: moving the king or a rook, or capturing a rook, revokes rights
    revoked = set()
    if piece[1] == "K":
        revoked |= {"K", "Q"} if color == "w" else {"k", "q"}
    for sq, right in ((0, "Q"), (7, "K"), (56, "q"), (63, "k")):
        if move.from_sq == sq or move.to_sq == sq:
            revoked.add(right)
    if revoked:
        new.castling_rights = new.castling_rights - revoked

    new.halfmove_clock = 0 if (is_capture or is_pawn_move) else board.halfmove_clock + 1
    if color == "b":
        new.fullmove_number += 1
    new.to_move = opponent

    return new


def generate_legal_moves(board: Board) -> List[Move]:
    color = board.to_move
    legal = []
    for move in generate_pseudo_legal_moves(board):
        resulting = apply_move(board, move)
        if not is_in_check(resulting, color):
            legal.append(move)
    return legal


def is_checkmate(board: Board) -> bool:
    return is_in_check(board, board.to_move) and not generate_legal_moves(board)


def is_stalemate(board: Board) -> bool:
    return not is_in_check(board, board.to_move) and not generate_legal_moves(board)
