#!/usr/bin/env python3
"""A tiny git-alike CLI: init, commit, log, checkout, diff, branch."""
import argparse
import sys
import time
from pathlib import Path

from vcs import Repository, RepositoryError, diff_trees, hash_object
from vcs.commit import read_commit, serialize_commit


def cmd_init(args) -> int:
    Repository.init(Path(args.path))
    print(f"initialized empty repository in {args.path}/.vcs")
    return 0


def cmd_commit(args) -> int:
    repo = Repository.open(Path("."))
    commit_hash = repo.commit(args.message)
    print(commit_hash)
    return 0


def cmd_log(args) -> int:
    repo = Repository.open(Path("."))
    for commit_obj in repo.log():
        commit_hash = hash_object("commit", serialize_commit(commit_obj))
        when = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(commit_obj.timestamp))
        print(f"{commit_hash[:10]}  {when}  {commit_obj.message}")
    return 0


def cmd_checkout(args) -> int:
    repo = Repository.open(Path("."))
    target = Path(args.target) if args.target else None
    repo.checkout(args.commit, target)
    print(f"checked out {args.commit[:10]} into {args.target or '.'}")
    return 0


def cmd_diff(args) -> int:
    repo = Repository.open(Path("."))
    tree_a = read_commit(repo.store, args.commit_a).tree_hash
    tree_b = read_commit(repo.store, args.commit_b).tree_hash
    for status, path in diff_trees(repo.store, tree_a, tree_b):
        print(f"{status:9s} {path}")
    return 0


def cmd_branch(args) -> int:
    repo = Repository.open(Path("."))
    if args.name:
        repo.create_branch(args.name)
        print(f"created branch {args.name}")
    else:
        current = repo.current_branch()
        for name in repo.branches():
            marker = "*" if name == current else " "
            print(f"{marker} {name}")
    return 0


def cmd_switch(args) -> int:
    repo = Repository.open(Path("."))
    repo.switch_branch(args.name)
    print(f"switched to branch {args.name}")
    return 0


def cmd_merge(args) -> int:
    repo = Repository.open(Path("."))
    commit_hash = repo.merge(args.branch, args.message)
    print(commit_hash)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("path", nargs="?", default=".")
    p_init.set_defaults(func=cmd_init)

    p_commit = sub.add_parser("commit")
    p_commit.add_argument("-m", "--message", required=True)
    p_commit.set_defaults(func=cmd_commit)

    p_log = sub.add_parser("log")
    p_log.set_defaults(func=cmd_log)

    p_checkout = sub.add_parser("checkout")
    p_checkout.add_argument("commit")
    p_checkout.add_argument("target", nargs="?")
    p_checkout.set_defaults(func=cmd_checkout)

    p_diff = sub.add_parser("diff")
    p_diff.add_argument("commit_a")
    p_diff.add_argument("commit_b")
    p_diff.set_defaults(func=cmd_diff)

    p_branch = sub.add_parser("branch")
    p_branch.add_argument("name", nargs="?")
    p_branch.set_defaults(func=cmd_branch)

    p_switch = sub.add_parser("switch")
    p_switch.add_argument("name")
    p_switch.set_defaults(func=cmd_switch)

    p_merge = sub.add_parser("merge")
    p_merge.add_argument("branch")
    p_merge.add_argument("-m", "--message", required=True)
    p_merge.set_defaults(func=cmd_merge)

    args = parser.parse_args()
    try:
        return args.func(args)
    except RepositoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
