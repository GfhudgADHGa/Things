# sudoku

A Sudoku solver and puzzle generator, from scratch: constraint-propagation
backtracking, uniqueness-checked puzzle generation, and a simple
technique-based difficulty rating.

```bash
python3 main.py generate --seed 1 --min-clues 26
python3 main.py solve "53..7....6..195....98....6.8...6...4..8.3..17...2...6.6....28....419..5....8..79"
```

## The solver

At each step, pick the empty cell with the **fewest remaining
candidates** (the most-constrained-variable heuristic) and try each one,
recursing. This is what makes wrong guesses fail fast: a cell with only
one legal candidate gets filled immediately with no branching at all, and
a cell with zero candidates is detected as a dead end the moment it
becomes most-constrained, rather than after wandering through the rest
of the board first.

## A real bug: "locally fine" isn't the same as "actually solvable"

An early test tried to check that the solver correctly reports an
unsolvable board by giving the same digit twice in one row:

```python
board[0] = 5
board[1] = 5
```

This should be rejected instantly — two 5s in a row can never be part of
a valid Sudoku. Instead, it made the test suite hang. The bug: the
backtracking search only ever checks a *new* placement against its
peers' *current* values — it never re-examines the original given cells
against each other. So neither `5` looks locally wrong to any other
cell: each empty peer just excludes `5` from its own candidate list once,
exactly as it would for any single ordinary given. The redundancy is
invisible to the search from the very first move, and it can spend an
enormous amount of time constructing an otherwise-plausible-looking
completion before it has explored every possibility and finally
concludes there's no solution.

The fix is a cheap upfront check: `solve()` and `count_solutions()` now
call `is_valid_board()` — no duplicate values in any row, column, or box
among the cells that are already filled in — before searching at all.
Two conflicting givens are now rejected in **microseconds** instead of
whatever multi-second-or-longer search it was doing before (measured
during development: still running after 8+ seconds and half a million
recursive calls with no end in sight). `test_solve_rejects_conflicting_
givens_instantly` in `tests/test_solver.py` asserts this stays under
100ms, specifically so a regression here fails loudly instead of just
quietly making the test suite slow again.

Note this doesn't make the solver *complete* in some deeper sense — a
board can still be arranged so that a particular *empty* cell has zero
candidates only once the search reaches it (an actual dead end
mid-search, not a given-vs-given conflict); that's the normal,
inexpensive case the most-constrained-variable heuristic already handles
well, and `test_solve_returns_none_for_unsolvable_board_with_a_dead_end_
cell` checks it explicitly.

## The generator

1. Fill a completely empty grid via the same backtracking search, but
   with candidate order shuffled — this produces a uniformly random
   *valid, complete* grid.
2. Remove givens one at a time, in random order. After each removal,
   check the puzzle still has **exactly one** solution (via
   `count_solutions(..., limit=2)`, which stops counting the moment it
   finds a second one — no need to enumerate every solution just to know
   there's more than one). If removing a cell breaks uniqueness, put it
   back. Keep going until `min_clues` is reached or every cell has been
   tried.

Difficulty is rated by how far pure logical elimination (repeatedly
filling in any cell that has exactly one legal candidate — a "naked
single," no guessing involved) gets before it stalls: fully solved this
way is `easy`; a handful of cells left over is `medium`; genuinely
needing backtracking/search is `hard`.

## Architecture

```
sudoku/
  board.py       flat 81-cell representation, parsing/printing, peers(),
                   validity checks
  solver.py         most-constrained-variable backtracking, solution
                     counting, the upfront validity short-circuit above
  generator.py       random valid grid -> uniqueness-checked puzzle,
                       difficulty rating
```

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

40 tests: board mechanics (peers, validity, parsing round-trips), the
solver (a known easy puzzle solved to its exact expected solution, given
clues always preserved, input never mutated, both flavors of
unsolvability above, performance on a hard 24-clue generated puzzle
staying under 5 seconds), and the generator (every generated puzzle
solves to a valid complete grid, is genuinely unique — checked across 15
different seeds, not just one — respects the requested minimum clue
count, and is deterministic given a seed).

## Possible expansions

- Human-style solving techniques beyond naked singles (hidden singles,
  naked/hidden pairs, pointing pairs) for a more discriminating
  difficulty rating than "how many cells are left when logic alone stalls"
- Symmetric givens (many published puzzles remove cells in a rotationally
  symmetric pattern purely for aesthetics)
- A minimal-clue-count search (the mathematically proven floor for a
  uniquely-solvable puzzle is 17 givens; this generator's `min_clues`
  floor is just a time-budget cutoff, not a search for that true minimum)
