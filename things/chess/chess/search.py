"""Minimax search with alpha-beta pruning (negamax formulation)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .board import Board
from .evaluate import evaluate
from .moves import Move, apply_move, generate_legal_moves, is_in_check

MATE_SCORE = 1_000_000.0


@dataclass
class SearchStats:
    nodes: int = 0


def _order_moves(board: Board, moves):
    """Cheap move ordering: try captures first (helps alpha-beta prune more)."""

    def is_capture(move: Move) -> bool:
        return board.squares[move.to_sq] is not None or move.is_en_passant

    return sorted(moves, key=is_capture, reverse=True)


def _negamax(board: Board, depth: int, alpha: float, beta: float, ply: int, stats: SearchStats) -> float:
    stats.nodes += 1
    moves = generate_legal_moves(board)

    if not moves:
        if is_in_check(board, board.to_move):
            return -(MATE_SCORE - ply)  # being mated: worse the sooner it happens
        return 0.0  # stalemate

    if depth == 0:
        perspective = 1 if board.to_move == "w" else -1
        return perspective * evaluate(board)

    best = float("-inf")
    for move in _order_moves(board, moves):
        score = -_negamax(apply_move(board, move), depth - 1, -beta, -alpha, ply + 1, stats)
        if score > best:
            best = score
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    return best


def find_best_move(board: Board, depth: int) -> Tuple[Optional[Move], float, SearchStats]:
    """Returns (best_move, score_from_side_to_move's_perspective, stats).

    best_move is None if there are no legal moves (checkmate or stalemate).
    """
    stats = SearchStats()
    moves = generate_legal_moves(board)
    if not moves:
        return None, 0.0, stats

    best_move = None
    best_score = float("-inf")
    alpha, beta = float("-inf"), float("inf")

    for move in _order_moves(board, moves):
        score = -_negamax(apply_move(board, move), depth - 1, -beta, -alpha, 1, stats)
        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, score)

    return best_move, best_score, stats
