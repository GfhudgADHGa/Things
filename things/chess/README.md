# chess

A chess engine from scratch: full legal move generation (including castling,
en passant, and promotion), minimax search with alpha-beta pruning, a simple
material + piece-square evaluation, and a text UI to play against it.

```bash
python3 main.py                    # play White vs. the engine (depth 3)
python3 main.py --color b          # play Black instead
python3 main.py --depth 4          # stronger (slower) engine, fixed depth
python3 main.py --time 2.0         # iterative deepening, 2 seconds per move
python3 main.py --fen "<FEN>"      # start from a custom position
```

Enter moves in coordinate notation: `e2e4`, `e7e8q` (promote to queen),
`e1g1` (castling — just move the king two squares, like any GUI). Type `q`
to quit.

## Correctness: perft

Move generation is the part most likely to have a subtle bug (an illegal
castle, a missed pin, a wrong en passant square), and those bugs don't
announce themselves — they just make some games play weird. The standard
way to catch them is **perft**: count every leaf node in the full legal
move tree to a given depth, and compare against known-correct reference
counts.

```
perft(1) = 20        perft(2) = 400        perft(3) = 8902       perft(4) = 197281
```

for the starting position, and, for the "Kiwipete" position (a stress test
for castling rights, en passant, and pins:
`r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`):

```
perft(1) = 48         perft(2) = 2039        perft(3) = 97862
```

Both match the standard published values exactly — see `tests/test_moves.py`.
`chess/perft.py` is 8 lines; trust in the move generator comes entirely from
matching these numbers, not from reading the code and believing it.

## Architecture

```
chess/
  board.py       8x8 array board state, FEN import/export
  moves.py        pseudo-legal move generation per piece, legality
                   filtering (simulate + check own king), attack detection
  perft.py         perft(board, depth) — the correctness harness above
  evaluate.py      material + piece-square-table static evaluation
  zobrist.py         Zobrist hashing: one 64-bit int identifying a position
  search.py         negamax + alpha-beta, a Zobrist-keyed transposition
                     table, iterative deepening, capture-first move ordering
  cli.py             text UI: render board, parse/validate input, play loop
```

**Board**: squares are `None` or a 2-character string like `"wN"`. Simple
and readable over bitboards, at some performance cost — fine for a
few-ply search in Python.

**Move generation** is pseudo-legal generation (each piece's normal moves,
ignoring whether it leaves your own king in check) followed by a legality
filter that actually plays each move and checks the resulting position.
This is the simplest correct approach, and perft confirms it's actually
correct rather than just plausible.

**Search** is textbook negamax + alpha-beta: at each node, try moves in
an order that tries the transposition table's remembered best move first,
then captures, then everything else, recurse with negated and swapped
alpha/beta bounds, and prune once a move proves "too good to be reached"
by the opponent. Depth 3-4 plays reasonably; it is not trying to be a
strong engine, just a correct and readable one.

### Transposition table

Different move orders often reach the identical position (1.Nf3 Nf6
2.Ng1 Ng8 is back to the start) — a "transposition." `zobrist.py` gives
every position a single 64-bit hash (XOR-ing precomputed random keys for
each piece-on-square, side to move, castling rights, and en passant
file), and `search.py` uses that hash to cache each position's search
result: the score, whether it's exact or a bound, the depth it was
searched to, and the best move found. A later visit to the same position
at a sufficient depth reuses that result instead of re-exploring the
whole subtree.

Measured directly on the Kiwipete position (`tests/test_transposition.py`
pins down the qualitative claims; these exact counts are from manual
A/B profiling during development, with the hash function replaced by a
counter that never matches to simulate "no TT"):

| depth | nodes, no TT | nodes, with TT | TT hits |
|---|---|---|---|
| 4 | 6,605 | 5,810 | 793 |
| 5 | 58,894 | 50,897 | 1,709 |

A real but modest win at this shallow depth (~14% fewer nodes) — the
transposition table's payoff grows with search depth, since deeper
searches have exponentially more paths that can converge on the same
position.

### Iterative deepening

`find_best_move_iterative(board, max_depth, time_limit_seconds)` searches
depth 1, then 2, then 3, ... up to `max_depth` or until the time budget
runs out, reusing one transposition table across every iteration. Two
real benefits, neither of which is "fewer total nodes" (searching every
shallow depth on the way to depth N costs more nodes overall than jumping
straight to depth N — confirmed by profiling, not assumed):

1. **Anytime behavior.** Under a real time budget, a search that gets
   interrupted mid-depth is useless (no complete picture of the root
   moves). Iterative deepening always has a complete, trustworthy answer
   from the last *finished* depth, ready to return the moment the clock
   runs out.
2. **Better move ordering at the deepest ply.** Each shallow iteration's
   TT entries seed move ordering for the next, deeper one. On Kiwipete,
   the depth-5 iteration alone (running with a TT already warmed by
   depths 1-4) explored 49,964 nodes, versus 50,897 for a cold direct
   depth-5 search — a modest but real improvement from ordering alone,
   on top of the anytime property.

It also stops early once a forced mate is found (searching deeper past a
confirmed mate can't change the decision) — see
`test_iterative_deepening_stops_searching_deeper_once_mate_found`.

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

67 tests: perft at multiple depths on two positions, FEN round-tripping,
targeted rule tests (en passant, all four promotion pieces, castling
availability/unavailability including "through check", pins, forced
check response, checkmate/stalemate detection), evaluation symmetry and
material comparison, search sanity (finds a known mate-in-1, doesn't
hang a queen for free, always returns a legal move), Zobrist hashing
(identical positions hash identically including via a real transposition,
different positions/side-to-move/castling-rights/en-passant hash
differently), and the transposition table + iterative deepening (TT hits
are real and nonzero at depth 4+, iterative deepening respects a time
budget, stops early on a found mate, and always returns a legal move).

## Possible expansions

- Quiescence search (extend search through captures at leaf nodes, so the
  engine doesn't misjudge a position mid-exchange)
- A proper replacement policy for the transposition table (currently
  unbounded — every position searched gets an entry, with no eviction)
- UCI protocol support to plug into a real chess GUI
