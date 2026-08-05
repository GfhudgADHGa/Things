"""Minimax search with alpha-beta pruning (negamax formulation), a
transposition table keyed by Zobrist hash, and iterative deepening.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from .board import Board
from .evaluate import evaluate
from .moves import Move, apply_move, generate_legal_moves, is_in_check
from .zobrist import zobrist_hash

MATE_SCORE = 1_000_000.0

EXACT = "EXACT"
LOWERBOUND = "LOWERBOUND"
UPPERBOUND = "UPPERBOUND"


@dataclass
class TTEntry:
    depth: int
    score: float
    flag: str
    best_move: Optional[Move]


TranspositionTable = Dict[int, TTEntry]


@dataclass
class SearchStats:
    nodes: int = 0
    tt_hits: int = 0


def _order_moves(board: Board, moves, hint_move: Optional[Move] = None):
    """Cheap move ordering: the transposition table's remembered best move
    first (if any), then captures, then everything else -- better ordering
    means alpha-beta prunes more of the tree.
    """

    def key(move: Move):
        is_hint = move == hint_move
        is_capture = board.squares[move.to_sq] is not None or move.is_en_passant
        return (is_hint, is_capture)

    return sorted(moves, key=key, reverse=True)


def _negamax(
    board: Board, depth: int, alpha: float, beta: float, ply: int, stats: SearchStats, tt: TranspositionTable
) -> float:
    stats.nodes += 1
    original_alpha = alpha

    key = zobrist_hash(board)
    entry = tt.get(key)
    if entry is not None and entry.depth >= depth:
        stats.tt_hits += 1
        if entry.flag == EXACT:
            return entry.score
        elif entry.flag == LOWERBOUND:
            alpha = max(alpha, entry.score)
        elif entry.flag == UPPERBOUND:
            beta = min(beta, entry.score)
        if alpha >= beta:
            return entry.score

    moves = generate_legal_moves(board)
    if not moves:
        if is_in_check(board, board.to_move):
            return -(MATE_SCORE - ply)
        return 0.0

    if depth == 0:
        perspective = 1 if board.to_move == "w" else -1
        return perspective * evaluate(board)

    hint = entry.best_move if entry is not None else None
    best = float("-inf")
    best_move_here: Optional[Move] = None
    for move in _order_moves(board, moves, hint):
        score = -_negamax(apply_move(board, move), depth - 1, -beta, -alpha, ply + 1, stats, tt)
        if score > best:
            best = score
            best_move_here = move
        alpha = max(alpha, score)
        if alpha >= beta:
            break

    if best <= original_alpha:
        flag = UPPERBOUND
    elif best >= beta:
        flag = LOWERBOUND
    else:
        flag = EXACT
    tt[key] = TTEntry(depth, best, flag, best_move_here)

    return best


def find_best_move(board: Board, depth: int) -> Tuple[Optional[Move], float, SearchStats]:
    """Fixed-depth search. Returns (best_move, score_from_side_to_move's
    perspective, stats). best_move is None if there are no legal moves.
    """
    stats = SearchStats()
    tt: TranspositionTable = {}
    moves = generate_legal_moves(board)
    if not moves:
        return None, 0.0, stats

    best_move = None
    best_score = float("-inf")
    alpha, beta = float("-inf"), float("inf")

    for move in _order_moves(board, moves):
        score = -_negamax(apply_move(board, move), depth - 1, -beta, -alpha, 1, stats, tt)
        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, score)

    return best_move, best_score, stats


def find_best_move_iterative(
    board: Board, max_depth: int = 20, time_limit_seconds: Optional[float] = None
) -> Tuple[Optional[Move], float, SearchStats, int]:
    """Iterative deepening: searches depth 1, 2, 3, ... reusing one
    transposition table across iterations, so each deeper search benefits
    from move ordering learned by the previous (cheaper) one. Stops at
    max_depth, or as soon as time_limit_seconds has elapsed (returning the
    best result from the deepest *completed* iteration -- a search cut off
    mid-iteration is discarded, since it hasn't examined every root move
    and so can't be trusted as "best").

    Returns (best_move, score, stats, depth_reached).
    """
    stats = SearchStats()
    tt: TranspositionTable = {}
    start = time.time()

    moves = generate_legal_moves(board)
    if not moves:
        return None, 0.0, stats, 0

    best_move: Optional[Move] = None
    best_score = 0.0
    depth_reached = 0

    for depth in range(1, max_depth + 1):
        if time_limit_seconds is not None and time.time() - start > time_limit_seconds:
            break

        alpha, beta = float("-inf"), float("inf")
        iteration_best_move = None
        iteration_best_score = float("-inf")

        for move in _order_moves(board, moves, best_move):
            score = -_negamax(apply_move(board, move), depth - 1, -beta, -alpha, 1, stats, tt)
            if score > iteration_best_score:
                iteration_best_score = score
                iteration_best_move = move
            alpha = max(alpha, score)

        best_move = iteration_best_move
        best_score = iteration_best_score
        depth_reached = depth

        if best_score >= MATE_SCORE - 1000:
            break  # found a forced mate; searching deeper won't change the decision

    return best_move, best_score, stats, depth_reached
