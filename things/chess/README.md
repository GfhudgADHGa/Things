# chess

A chess engine from scratch: full legal move generation (including castling,
en passant, and promotion), minimax search with alpha-beta pruning, a simple
material + piece-square evaluation, and a text UI to play against it.

```bash
python3 main.py                    # play White vs. the engine (depth 3)
python3 main.py --color b          # play Black instead
python3 main.py --depth 4          # stronger (slower) engine
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
  search.py         negamax with alpha-beta pruning, capture-first move
                     ordering, mate-distance scoring
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
an order that tries captures first (a cheap heuristic that lets alpha-beta
cut off far more of the tree), recurse with negated and swapped
alpha/beta bounds, and prune once a move proves "too good to be reached"
by the opponent. Depth 3-4 plays reasonably; it is not trying to be a
strong engine, just a correct and readable one.

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

50 tests: perft at multiple depths on two positions, FEN round-tripping,
targeted rule tests (en passant, all four promotion pieces, castling
availability/unavailability including "through check", pins, forced
check response, checkmate/stalemate detection), evaluation symmetry and
material comparison, and search sanity (finds a known mate-in-1, doesn't
hang a queen for free, always returns a legal move).

## Possible expansions

- Quiescence search (extend search through captures at leaf nodes, so the
  engine doesn't misjudge a position mid-exchange)
- Transposition table
- Iterative deepening with a time budget instead of a fixed depth
- UCI protocol support to plug into a real chess GUI
