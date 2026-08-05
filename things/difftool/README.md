# difftool

A line-based diff/patch tool built on Myers' O(ND) shortest-edit-script
algorithm — the same core algorithm behind `diff`, `git diff`, and most
other line-diffing tools.

```bash
python3 main.py file_a.txt file_b.txt
```

```
 one
-two
+TWO
 three
-four
+five
```

## The algorithm

Think of turning `a` into `b` as a path through an `(x, y)` grid from
`(0, 0)` to `(len(a), len(b))`: a right-move deletes `a[x]`, a down-move
inserts `b[y]`, and a diagonal move keeps a line that matches in both —
free, since it's not an edit. The shortest edit script is just the
shortest such path.

Myers' algorithm finds it without ever exploring the full grid: for each
possible edit distance `D = 0, 1, 2, ...`, it tracks the furthest `x`
reachable on each diagonal `k = x - y` using exactly `D` non-diagonal
moves, always extending every diagonal move as far as it'll go for free
first. The moment some diagonal's frontier reaches the far corner, `D`
is the true minimum edit distance, and backtracking through the
recorded frontiers reconstructs the actual script. This runs in
`O((len(a) + len(b)) * D)` time — fast whenever the inputs are similar
(small `D`), which is exactly the common case for diffing two versions
of the same file.

## A test that was wrong, not the code

An early correctness check compared `myers_diff`'s edit count directly
against Python's own `difflib.SequenceMatcher` and found frequent,
sometimes large, mismatches in *both* directions — Myers sometimes
"worse," sometimes "better." That's not actually a valid comparison:
`difflib` uses a different algorithm (Ratcliff/Obershelp pattern
matching, with "autojunk" heuristics) and does **not** guarantee a
minimal edit script — it optimizes for producing human-readable diffs,
not the shortest possible one. So Myers finding a shorter script than
difflib isn't a bug, it's the point.

Finding *more* edits than difflib would have been a real problem, though
— Myers is provably minimal, so it should never need more edits than any
other valid script, difflib's included. Checking specifically for that
direction turned up nothing across 500 random cases — except the
comparison itself had a bug: it costed a difflib `'replace'` opcode as
`max(deleted, inserted)` instead of `deleted + inserted`, which is the
correct cost under the insert/delete-only edit model `myers_diff`
actually uses (no dedicated "substitute" primitive). Once the comparison
used the right formula, Myers was never worse than difflib on any of
500 random trials — consistent with the optimality the algorithm
promises. See `test_myers_is_never_worse_than_difflib_across_many_random_cases`
in `tests/test_diff.py`.

## Usage

```python
from difftool import myers_diff, format_diff, apply_patch

a = ["one", "two", "three"]
b = ["one", "TWO", "three"]

ops = myers_diff(a, b)
print(format_diff(ops))
# " one\n-two\n+TWO\n three"

assert apply_patch(a, ops) == b
```

`apply_patch` validates as it goes — it checks each `equal`/`delete`
line in the script against the actual source, and raises `PatchError`
if they don't match (a patch generated against a different version of
the file) or if there are leftover/missing source lines. It doesn't
silently produce garbage from a mismatched patch.

## Architecture

```
difftool/
  diff.py       myers_diff(): the O(ND) algorithm and backtracking
  format.py       unified-diff-style rendering (' '/'-'/'+') and parsing
  patch.py         apply_patch(): reconstruct b from a + an edit script,
                     validated against the actual source
```

Scope note: lines are assumed not to contain embedded newlines (the
normal case for line-based diffing via `str.splitlines()`) — the
`format`/`parse` round-trip uses `\n` as the op separator.

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

28 tests: diff correctness (identical/empty/disjoint sequences, a hand-
computed LCS-based expected edit distance, the difflib-minimality
cross-check above), round-tripping (`myers_diff` -> extracting the `a`-
and `b`-views always reconstructs the originals, across 300+ random
cases and a parametrized sweep of input sizes), format/parse
round-tripping, and patch application (successful reconstruction,
rejecting a mismatched/shorter/longer source, 300 random diff-then-patch
round trips).

## Possible expansions

- Word-level or character-level diffing (currently line-level only)
- A real substitution/replace primitive instead of paired delete+insert,
  for more compact output on modified (not just added/removed) lines
- Context-limited unified diff output (`@@ -l,s +l,s @@` hunks showing
  only N lines of surrounding context, like real `diff -u`) instead of
  the whole file
