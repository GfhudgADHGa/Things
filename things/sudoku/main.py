#!/usr/bin/env python3
"""Generate or solve Sudoku puzzles from the command line."""
from __future__ import annotations

import argparse
import sys

from sudoku import generate_puzzle, parse, pretty, rate_difficulty, solve, to_string


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="generate a new puzzle")
    g.add_argument("--seed", type=int, default=None)
    g.add_argument("--min-clues", type=int, default=28)

    s = sub.add_parser("solve", help="solve a puzzle given as an 81-character string")
    s.add_argument("puzzle")

    args = parser.parse_args()

    if args.command == "generate":
        puzzle = generate_puzzle(seed=args.seed, min_clues=args.min_clues)
        print(pretty(puzzle))
        print()
        print(f"clues: {sum(1 for v in puzzle if v)}  difficulty: {rate_difficulty(puzzle)}")
        print(to_string(puzzle))

    elif args.command == "solve":
        board = parse(args.puzzle)
        result = solve(board)
        if result is None:
            print("no solution")
            return 1
        print(pretty(result))

    return 0


if __name__ == "__main__":
    sys.exit(main())
