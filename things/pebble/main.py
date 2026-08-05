#!/usr/bin/env python3
import argparse
import sys

from pebble.cli import repl, run_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Pebble script, or start the REPL.")
    parser.add_argument("script", nargs="?", help="path to a .pebble file; omit for the REPL")
    parser.add_argument(
        "--vm", action="store_true",
        help="execute via the bytecode compiler+VM instead of the tree-walking interpreter",
    )
    args = parser.parse_args()

    if args.script:
        return run_file(args.script, use_vm=args.vm)
    repl()
    return 0


if __name__ == "__main__":
    sys.exit(main())
