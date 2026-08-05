"""A simple text UI: play against the engine, or watch it play itself."""
from __future__ import annotations

import argparse
import sys

from .board import Board, STARTING_FEN, square_from_name
from .moves import (
    Move,
    apply_move,
    generate_legal_moves,
    is_checkmate,
    is_in_check,
    is_stalemate,
)
from .search import find_best_move, find_best_move_iterative

PIECE_GLYPHS = {
    "wP": "P", "wN": "N", "wB": "B", "wR": "R", "wQ": "Q", "wK": "K",
    "bP": "p", "bN": "n", "bB": "b", "bR": "r", "bQ": "q", "bK": "k",
}


def render(board: Board) -> str:
    lines = []
    for rank in range(7, -1, -1):
        cells = []
        for file in range(8):
            piece = board.squares[rank * 8 + file]
            cells.append(PIECE_GLYPHS[piece] if piece else ".")
        lines.append(f"{rank + 1} " + " ".join(cells))
    lines.append("  " + " ".join("abcdefgh"))
    return "\n".join(lines)


def parse_move_input(board: Board, text: str) -> Move | None:
    text = text.strip().lower()
    if len(text) not in (4, 5):
        return None
    try:
        from_sq = square_from_name(text[0:2])
        to_sq = square_from_name(text[2:4])
    except (ValueError, IndexError):
        return None
    promotion = text[4].upper() if len(text) == 5 else None

    for move in generate_legal_moves(board):
        if move.from_sq != from_sq or move.to_sq != to_sq:
            continue
        if move.promotion is None or move.promotion == promotion:
            return move
    return None


def game_status_message(board: Board) -> str | None:
    if is_checkmate(board):
        winner = "Black" if board.to_move == "w" else "White"
        return f"Checkmate. {winner} wins."
    if is_stalemate(board):
        return "Stalemate. Draw."
    if board.halfmove_clock >= 100:
        return "Draw by 50-move rule."
    return None


def play(fen: str, human_color: str, depth: int, time_limit: float | None) -> None:
    board = Board.from_fen(fen)

    while True:
        print()
        print(render(board))
        status = game_status_message(board)
        if status:
            print(status)
            return

        if is_in_check(board, board.to_move):
            print(f"{'White' if board.to_move == 'w' else 'Black'} is in check.")

        if board.to_move == human_color:
            text = input(f"Your move ({board.to_move} to move, e.g. e2e4, q to quit): ")
            if text.strip().lower() in ("q", "quit", "exit"):
                return
            move = parse_move_input(board, text)
            if move is None:
                print("Illegal or unparseable move. Try again.")
                continue
            board = apply_move(board, move)
        else:
            print("Engine is thinking...")
            if time_limit is not None:
                move, score, stats, depth_reached = find_best_move_iterative(board, time_limit_seconds=time_limit)
                if move is None:
                    return
                print(f"Engine plays {move.to_uci()} (eval {score:+.0f}cp, depth {depth_reached}, {stats.nodes} nodes)")
            else:
                move, score, stats = find_best_move(board, depth)
                if move is None:
                    return
                print(f"Engine plays {move.to_uci()} (eval {score:+.0f}cp, {stats.nodes} nodes)")
            board = apply_move(board, move)


def main() -> int:
    parser = argparse.ArgumentParser(description="Play chess against a simple engine.")
    parser.add_argument("--fen", default=STARTING_FEN)
    parser.add_argument("--color", choices=["w", "b"], default="w", help="which side you play")
    parser.add_argument("--depth", type=int, default=3, help="engine search depth (plies)")
    parser.add_argument(
        "--time", type=float, default=None,
        help="if set, use iterative deepening with this many seconds per move instead of --depth",
    )
    args = parser.parse_args()

    play(args.fen, args.color, args.depth, args.time)
    return 0


if __name__ == "__main__":
    sys.exit(main())
