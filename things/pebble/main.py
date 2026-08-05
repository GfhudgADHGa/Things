#!/usr/bin/env python3
import sys

from pebble.cli import repl, run_file


def main() -> int:
    if len(sys.argv) > 2:
        print("usage: main.py [script.pebble]", file=sys.stderr)
        return 64
    if len(sys.argv) == 2:
        return run_file(sys.argv[1])
    repl()
    return 0


if __name__ == "__main__":
    sys.exit(main())
