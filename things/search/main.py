#!/usr/bin/env python3
"""Index a directory of text files and either run one query or start an
interactive search REPL."""
import argparse
import pathlib

from search import SearchEngine


def build_engine(directory: str) -> tuple:
    engine = SearchEngine()
    doc_id_to_path = {}
    paths = sorted(pathlib.Path(directory).glob("**/*.txt"))
    for doc_id, path in enumerate(paths):
        text = path.read_text(errors="replace")
        engine.add_document(doc_id, text)
        doc_id_to_path[doc_id] = path
    return engine, doc_id_to_path


def run_query(engine: SearchEngine, doc_id_to_path: dict, query: str, top_k: int) -> None:
    results = engine.search(query, top_k=top_k)
    if not results:
        print("no matches")
        return
    for doc_id, score in results:
        path = doc_id_to_path[doc_id]
        print(f"{score:8.4f}  {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="directory of .txt files to index (recursive)")
    parser.add_argument("query", nargs="?", help="run one query and exit; omit for an interactive REPL")
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    engine, doc_id_to_path = build_engine(args.directory)
    print(f"indexed {len(doc_id_to_path)} documents from {args.directory}")

    if args.query:
        run_query(engine, doc_id_to_path, args.query, args.top_k)
        return 0

    print('interactive mode -- type a query, or "quit" to exit')
    while True:
        try:
            query = input("search> ")
        except EOFError:
            print()
            break
        if query.strip() in ("quit", "exit"):
            break
        if query.strip():
            run_query(engine, doc_id_to_path, query, args.top_k)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
