#!/usr/bin/env python3
"""CLI for minidb: run a .sql script, or start an interactive REPL."""
import argparse
import sys

from minidb import Database, MiniDBError, QueryResult, execute, parse_many


def _format_value(value) -> str:
    return "NULL" if value is None else str(value)


def _print_result(result: QueryResult) -> None:
    if not result.rows:
        print(f"({', '.join(result.headers)})")
        print("0 rows")
        return
    widths = [len(h) for h in result.headers]
    str_rows = [[_format_value(v) for v in row] for row in result.rows]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(result.headers))
    print(header_line)
    print("-+-".join("-" * w for w in widths))
    for row in str_rows:
        print(" | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
    print(f"{len(result.rows)} row{'s' if len(result.rows) != 1 else ''}")


def run_statement(db: Database, sql: str) -> None:
    for stmt in parse_many(sql):
        result = execute(db, stmt)
        if isinstance(result, QueryResult):
            _print_result(result)
        elif isinstance(result, int):
            print(f"OK ({result} row{'s' if result != 1 else ''} affected)")
        else:
            print("OK")


def run_script(db: Database, text: str) -> int:
    try:
        run_statement(db, text)
    except MiniDBError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def repl(db: Database) -> None:
    print("minidb -- type SQL statements ending in ';'. Ctrl-D to exit.")
    buffer = ""
    while True:
        try:
            prompt = "minidb> " if not buffer else "     -> "
            line = input(prompt)
        except EOFError:
            print()
            break
        buffer += line + "\n"
        if ";" in line:
            try:
                run_statement(db, buffer)
            except MiniDBError as exc:
                print(f"error: {exc}")
            buffer = ""


def main() -> int:
    parser = argparse.ArgumentParser(description="minidb: a small SQL engine from scratch")
    parser.add_argument("script", nargs="?", help="path to a .sql file to run non-interactively")
    args = parser.parse_args()

    db = Database()
    if args.script:
        with open(args.script) as f:
            text = f.read()
        return run_script(db, text)
    repl(db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
