#!/usr/bin/env python3
"""CLI: search a file (or stdin) for lines matching a pattern, grep-style."""
from __future__ import annotations

import argparse
import sys

import regex


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pattern")
    parser.add_argument("file", nargs="?", help="defaults to stdin")
    args = parser.parse_args()

    try:
        compiled = regex.compile(args.pattern)
    except regex.RegexSyntaxError as e:
        print(f"regex: {e}", file=sys.stderr)
        return 1

    lines = open(args.file) if args.file else sys.stdin
    found_any = False
    for line in lines:
        line = line.rstrip("\n")
        if compiled.search(line) is not None:
            print(line)
            found_any = True

    return 0 if found_any else 1


if __name__ == "__main__":
    sys.exit(main())
