# vcs

A minimal git-alike version control system: a content-addressable
object store (blobs, trees, commits, all identified by the SHA-256 hash
of their own content), commit history as a real multi-parent DAG,
branches, a deliberately minimal merge, and file-level diffing.

```bash
python3 main.py init myrepo && cd myrepo
echo "hello" > a.txt && python3 ../main.py commit -m "first commit"
echo "hello, updated" > a.txt && python3 ../main.py commit -m "second commit"
python3 ../main.py log
```

## The correctness proof: round-trip fidelity

A version control system's one non-negotiable job is to never silently
lose or corrupt what you committed. So the main proof here
(`test_repository.py`) is exactly that: commit an arbitrary — including
randomly generated, arbitrarily nested — directory tree, check it out
into a completely fresh directory, and require the result to be
byte-for-byte identical to the original: same filenames, same nesting,
same file contents down to embedded null bytes and empty files. 40
randomized trials generate random directory structures (random depth,
random file counts, random binary content) and check this holds every
time — the same "prove the whole pipeline actually preserves what you
put into it" idea as `kvstore`'s crash-recovery tests and `jpeg`'s
Pillow round-trip, aimed at what this thing is actually for.

Content-addressing is checked directly too: committing two files with
identical content stores exactly one blob (not two), and re-committing
completely unchanged content only creates a new commit object — the
tree and every blob underneath it are already stored and get reused,
not duplicated.

## A real bug: a DFS that wasn't a topological sort

`commit_history()` walks the commit DAG and must return every ancestor
with each commit appearing *before* all of its own parents — the
natural definition of `log` order. The first implementation was a plain
iterative DFS that skipped anything already visited, which works
perfectly for a linear chain and *looks* obviously correct. It fails on
a diamond: two branches that both descend from the same shared ancestor
and later merge back together. Whichever branch's DFS happened to reach
the shared ancestor first would emit it immediately — potentially
*before* the other branch (which also points to that same ancestor, but
hadn't been processed yet) got emitted itself. `test_commit.py`'s
`test_diamond_merge_history_includes_each_commit_exactly_once` catches
this directly by checking every parent-child position, not just "is the
right set of commits present." The fix is the standard one: a real DFS
**post-order** (append a node only once every one of its parents has
been fully processed), then reverse it — the textbook way to
topologically sort a DAG, done iteratively (an explicit stack, not
Python recursion) so it doesn't hit the recursion limit on a long
history either, which a 5,000-commit test checks separately.

## Architecture

```
vcs/
  objects.py       ObjectStore: content-addressable blob storage,
                      store()/load() keyed by sha256(header + content)
  tree.py            TreeEntry, write_tree()/read_tree()/checkout_tree(),
                        flatten_tree() for diffing
  commit.py            Commit, serialize/deserialize, commit_history()
                          (the topological sort discussed above)
  diff.py                file-level diff between two committed trees
                          (added/removed/modified) -- not line-level;
                          see `difftool` elsewhere in this collection
                          for Myers line diffing
  repository.py            Repository: the high-level API tying
                              everything to a working directory, HEAD,
                              and branch refs
```

## What's supported

`init`, `commit`, `log` (topologically ordered, correct across merges),
`checkout` (into a fresh directory), `diff` (file-level, between any two
commits), `branch`/`switch`, and `merge` (records a real two-parent
commit; ancestry and diffing both work correctly across it).
**Not supported**: automatic content merging or conflict resolution
(`merge` just commits whatever's currently in the working directory —
you decide what the merged content looks like), a staging area/index
(every commit snapshots the whole working directory), remotes, and
`checkout` doesn't delete files that exist in the target directory but
aren't part of the committed tree (an overlay, not a full working-tree
reset) — using a fresh empty directory for checkout side-steps this,
which is exactly what every test here does.

## Usage

```bash
python3 main.py init myrepo
cd myrepo
python3 ../main.py commit -m "message"
python3 ../main.py log
python3 ../main.py checkout <commit-hash> [target-dir]
python3 ../main.py diff <commit-a> <commit-b>
python3 ../main.py branch [name]     # list, or create if a name is given
python3 ../main.py switch <name>
python3 ../main.py merge <branch> -m "message"
```

Or as a library:

```python
from pathlib import Path
from vcs import Repository

repo = Repository.init(Path("myrepo"))
(Path("myrepo") / "a.txt").write_text("hello")
commit_hash = repo.commit("first commit")
repo.checkout(commit_hash, Path("elsewhere"))  # byte-for-byte identical
```

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

88 tests: the object store (dedup, binary content with embedded nulls,
unknown-hash lookups), tree serialization and directory hashing
(identical directory contents always hash identically, regardless of
filesystem listing order), commit serialization and the DAG traversal
described above (including the diamond-history regression test and a
5,000-commit recursion-limit check), file-level diffing, and
`test_repository.py`'s round-trip fidelity and dedup proofs, branches,
and merges.

## Possible expansions

- A staging area (`add`), so a commit doesn't have to snapshot the
  entire working directory every time
- Real content merging with conflict markers instead of "whatever's in
  the working directory becomes the merge commit's tree"
- A proper working-tree reset on checkout (delete files not in the
  target tree, not just overlay)
- Object compression (objects are stored raw right now, unlike
  `huffman`'s general-purpose compressor elsewhere in this collection,
  which this could reuse the *idea* of without importing it directly)
