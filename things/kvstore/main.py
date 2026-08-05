#!/usr/bin/env python3
"""A REPL for the durable key-value store."""
from __future__ import annotations

import argparse
import os
import shlex
import sys

from kvstore import KVStore


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default="kvstore.db")
    args = parser.parse_args()

    with KVStore(args.path) as db:
        print(f"kvstore REPL on {args.path} ({len(db)} keys loaded). Commands:")
        print("  put <key> <value...>   get <key>   del <key>   keys   range [start] [end]   compact   quit")
        while True:
            try:
                line = input("> ")
            except EOFError:
                print()
                break

            try:
                parts = shlex.split(line)
            except ValueError as e:
                print(f"error: {e}")
                continue
            if not parts:
                continue

            cmd, args_ = parts[0], parts[1:]

            if cmd in ("quit", "exit", "q"):
                break
            elif cmd == "put":
                if len(args_) < 2:
                    print("usage: put <key> <value...>")
                    continue
                db.put(args_[0], " ".join(args_[1:]))
                print("ok")
            elif cmd == "get":
                if len(args_) != 1:
                    print("usage: get <key>")
                    continue
                value = db.get(args_[0])
                print(value if value is not None else "(nil)")
            elif cmd == "del":
                if len(args_) != 1:
                    print("usage: del <key>")
                    continue
                db.delete(args_[0])
                print("ok")
            elif cmd == "keys":
                for k in db.keys():
                    print(k)
            elif cmd == "range":
                if len(args_) > 2:
                    print("usage: range [start] [end]")
                    continue
                start = args_[0] if len(args_) >= 1 else None
                end = args_[1] if len(args_) >= 2 else None
                for k, v in db.range_query(start, end):
                    print(f"{k} = {v}")
            elif cmd == "compact":
                before = os.path.getsize(db.path)
                db.compact()
                after = os.path.getsize(db.path)
                print(f"compacted: {before} bytes -> {after} bytes")
            else:
                print(f"unknown command: {cmd}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
