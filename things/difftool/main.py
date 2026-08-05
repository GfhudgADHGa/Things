#!/usr/bin/env python3
"""Compares two files and prints a unified-diff-style script."""
from __future__ import annotations

import argparse
import sys

from difftool import edit_distance, format_diff, myers_diff


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file_a")
    parser.add_argument("file_b")
    args = parser.parse_args()

    with open(args.file_a) as f:
        a = f.read().splitlines()
    with open(args.file_b) as f:
        b = f.read().splitlines()

    ops = myers_diff(a, b)
    print(format_diff(ops))
    changed = sum(1 for op, _ in ops if op != "equal")
    print(f"\n{changed} line(s) changed ({edit_distance(a, b)} edits)", file=sys.stderr)

    return 0 if a == b else 1


if __name__ == "__main__":
    sys.exit(main())
