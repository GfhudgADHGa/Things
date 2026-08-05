#!/usr/bin/env python3
"""A gzip-like CLI: compress/decompress files with from-scratch Huffman coding."""
from __future__ import annotations

import argparse
import os
import sys

from huffman import compress, decompress


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("compress", help="compress a file to <input>.huf")
    c.add_argument("input")
    c.add_argument("-o", "--output")

    d = sub.add_parser("decompress", help="decompress a .huf file")
    d.add_argument("input")
    d.add_argument("-o", "--output")

    args = parser.parse_args()

    if args.command == "compress":
        output = args.output or args.input + ".huf"
        with open(args.input, "rb") as f:
            data = f.read()
        compressed = compress(data)
        with open(output, "wb") as f:
            f.write(compressed)
        ratio = len(compressed) / len(data) if data else 1.0
        print(f"{args.input}: {len(data)} -> {len(compressed)} bytes ({ratio:.1%}) -> {output}")

    elif args.command == "decompress":
        output = args.output or args.input.removesuffix(".huf")
        if output == args.input:
            output += ".out"
        with open(args.input, "rb") as f:
            data = f.read()
        restored = decompress(data)
        with open(output, "wb") as f:
            f.write(restored)
        print(f"{args.input}: {len(data)} -> {len(restored)} bytes -> {output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
