"""The high-level API: a working directory plus a `.vcs` metadata
directory holding the object store, branch refs, and HEAD."""
from __future__ import annotations

import time
from pathlib import Path
from typing import List, Optional

from .commit import Commit, commit_history, read_commit, write_commit
from .objects import ObjectStore
from .tree import checkout_tree, write_tree


class RepositoryError(Exception):
    pass


class Repository:
    VCS_DIR = ".vcs"

    def __init__(self, root: Path):
        self.root = Path(root)
        self.vcs_dir = self.root / self.VCS_DIR
        self.store = ObjectStore(self.vcs_dir / "objects")
        self.refs_dir = self.vcs_dir / "refs"
        self.head_file = self.vcs_dir / "HEAD"

    def _ignore(self, path: Path) -> bool:
        return path.name == self.VCS_DIR

    @classmethod
    def init(cls, root: Path) -> "Repository":
        repo = cls(root)
        repo.root.mkdir(parents=True, exist_ok=True)
        repo.refs_dir.mkdir(parents=True, exist_ok=True)
        if not repo.head_file.exists():
            repo.head_file.write_text("main\n")
        if not (repo.refs_dir / "main").exists():
            (repo.refs_dir / "main").write_text("")
        return repo

    @classmethod
    def open(cls, root: Path) -> "Repository":
        repo = cls(root)
        if not repo.vcs_dir.exists():
            raise RepositoryError(f"not a vcs repository: {root}")
        return repo

    def current_branch(self) -> str:
        return self.head_file.read_text().strip()

    def _branch_ref_path(self, branch: str) -> Path:
        return self.refs_dir / branch

    def branches(self) -> List[str]:
        return sorted(p.name for p in self.refs_dir.iterdir())

    def head_commit(self) -> Optional[str]:
        ref_path = self._branch_ref_path(self.current_branch())
        content = ref_path.read_text().strip() if ref_path.exists() else ""
        return content or None

    def commit(self, message: str, timestamp: Optional[float] = None) -> str:
        tree_hash = write_tree(self.store, self.root, self._ignore)
        parent = self.head_commit()
        parents = (parent,) if parent else ()
        commit_obj = Commit(
            tree_hash, parents, message, timestamp if timestamp is not None else time.time()
        )
        commit_hash = write_commit(self.store, commit_obj)
        self._branch_ref_path(self.current_branch()).write_text(commit_hash + "\n")
        return commit_hash

    def checkout(self, commit_hash: str, target_dir: Optional[Path] = None) -> None:
        commit_obj = read_commit(self.store, commit_hash)
        checkout_tree(self.store, commit_obj.tree_hash, target_dir if target_dir is not None else self.root)

    def log(self) -> List[Commit]:
        head = self.head_commit()
        if head is None:
            return []
        return [read_commit(self.store, h) for h in commit_history(self.store, head)]

    def create_branch(self, name: str, at_commit: Optional[str] = None) -> None:
        commit_hash = at_commit if at_commit is not None else self.head_commit()
        if commit_hash is None:
            raise RepositoryError("cannot create a branch with no commits yet")
        if self._branch_ref_path(name).exists():
            raise RepositoryError(f"branch already exists: {name}")
        self._branch_ref_path(name).write_text(commit_hash + "\n")

    def switch_branch(self, name: str) -> None:
        if not self._branch_ref_path(name).exists():
            raise RepositoryError(f"no such branch: {name}")
        self.head_file.write_text(name + "\n")

    def merge(self, other_branch: str, message: str, timestamp: Optional[float] = None) -> str:
        """A deliberately minimal merge: records a commit with two
        parents (the current branch's tip and other_branch's tip) whose
        own tree is just the current working directory's contents at
        merge time. There's no automatic content merging or conflict
        resolution here -- the caller is responsible for the working
        directory actually containing whatever merged content they
        want committed. What this *does* give you for free is a real
        multi-parent commit DAG: ancestry queries (commit_history) and
        diffing both work correctly across merges, which is the part
        worth proving (see test_commit.py's diamond-history tests)."""
        current = self.head_commit()
        if current is None:
            raise RepositoryError("cannot merge with no commits on the current branch")
        other_ref = self._branch_ref_path(other_branch)
        if not other_ref.exists():
            raise RepositoryError(f"no such branch: {other_branch}")
        other_commit = other_ref.read_text().strip()

        tree_hash = write_tree(self.store, self.root, self._ignore)
        commit_obj = Commit(
            tree_hash, (current, other_commit), message, timestamp if timestamp is not None else time.time()
        )
        commit_hash = write_commit(self.store, commit_obj)
        self._branch_ref_path(self.current_branch()).write_text(commit_hash + "\n")
        return commit_hash
