# Things

A growing collection of small, self-contained software projects. No overarching
theme beyond: build something real, make it work, test it, write it down.

Each project lives in its own directory under [`things/`](things/), with its
own README, dependencies, and test suite. Nothing here depends on anything
else in the repo.

## Catalog

| Thing | Description |
|---|---|
| [`raytracer`](things/raytracer/) | A ray tracer written from scratch in Python: spheres, planes, diffuse/metal/glass materials, shadows, reflections, anti-aliasing. Renders PNGs. |
| [`roguelike`](things/roguelike/) | A terminal dungeon crawler: procedural levels, fog of war, turn-based combat, A* monster chasing, leveling, save/load. Playable with `curses`. |
| [`pebble`](things/pebble/) | A small scripting language, implemented from scratch: hand-written lexer, recursive-descent parser, tree-walking interpreter with closures, and a second bytecode-VM execution path — which, measured honestly, turned out *slower*, not faster (with a real, different advantage instead). |
| [`chess`](things/chess/) | A chess engine: full legal move generation (verified against known perft values), alpha-beta search, playable from the terminal. |
| [`regex`](things/regex/) | A regex engine built on Thompson NFA construction — no backtracking, so it's immune to catastrophic ReDoS blowup (verified against Python's `re`, which isn't). |
| [`kvstore`](things/kvstore/) | A durable key-value store: fsync'd write-ahead log, crash-safe recovery (verified by literally corrupting the log file and checking recovery), atomic compaction, range queries. |
| [`procmusic`](things/procmusic/) | Algorithmic music generation from scratch: raw waveform synthesis, a hand-rolled WAV writer, music theory (scales/chords), a small composer, and synthesized drums (kick/snare/hi-hat, no samples). Produces actual playable songs. |
| [`physics2d`](things/physics2d/) | A 2D rigid-body physics simulation (gravity, elastic collisions) rendered to an animated GIF via a from-scratch LZW encoder — including a real encoder/decoder sync bug found and fixed using Pillow as a decode oracle. |
| [`huffman`](things/huffman/) | A general-purpose file compressor: from-scratch Huffman tree construction, a custom bit-packed file format, and a CLI. Real measured compression ratios, not just claimed ones. |
| [`sudoku`](things/sudoku/) | A constraint-propagation solver and uniqueness-checked puzzle generator — including a real "locally fine isn't the same as solvable" bug found when a hang turned an obviously-correct-looking unsolvability test into a half-million-node search. |
| [`difftool`](things/difftool/) | A line-based diff/patch tool on Myers' O(ND) shortest-edit-script algorithm, with a validating patch-apply and a corrected (initially wrong!) minimality cross-check against Python's `difflib`. |
| [`neuralnet`](things/neuralnet/) | A feedforward neural network from scratch (dense layers, backprop, SGD) — proven correct via numerical gradient checking (~2.7e-9 relative error) rather than just "the loss went down", plus an honest negative result: plain SGD doesn't converge on a spiral-classification task. |
| [`minidb`](things/minidb/) | A small SQL engine from scratch: tokenizer, recursive-descent parser, in-memory tables, and a query executor (WHERE/JOIN/GROUP BY/ORDER BY/aggregates) — verified by cross-checking every query against Python's own `sqlite3` module as an oracle, which caught two real semantic bugs (case-sensitive `LIKE`, floor- instead of truncating-division). |
| [`jpeg`](things/jpeg/) | A baseline JPEG encoder from scratch: block DCT, standard quantization/Huffman tables, and real JFIF file output — proven with a hand-derived closed-form check on the DCT itself (a constant block's transform must be exactly DC-only), then with Pillow as an independent decode oracle across sizes, qualities, and 20 randomized trials. |
| [`raft`](things/raft/) | A from-scratch Raft consensus implementation (leader election + log replication) plus a deterministic fault-injection network simulator — proven via 120 randomized trials of message loss, partitions, and leader crashes checking the Raft paper's actual safety invariants, which caught two real single-node-cluster edge-case bugs and one overly-strong test assertion along the way. |
| [`search`](things/search/) | A small text search engine: inverted index, BM25 ranking, and a boolean/phrase query language — verified by cross-checking every query against a from-scratch brute-force recomputation over the raw corpus (no index at all) across 165 randomized and hand-picked cases, plus a direct demonstration that classic BM25's IDF can go negative for very common terms. |
| [`crypto`](things/crypto/) | From-scratch SHA-256, HMAC-SHA256, and AES-128-CBC, built directly from their published specs (educational only, not constant-time) — verified bit-for-bit against Python's `hashlib`/`hmac` and, for AES, against both FIPS-197's own published test vector and the `cryptography` library as a live ciphertext-exact oracle. |
| [`vcs`](things/vcs/) | A minimal git-alike: a content-addressable object store, a real multi-parent commit DAG, branches, merges, and file-level diffing — proven via round-trip fidelity (commit a randomly generated nested directory tree, checkout to a fresh location, byte-for-byte identical) across 40 randomized trials, which caught a real bug in the commit-history topological sort on diamond-shaped (merge) histories. |
| [`fractal`](things/fractal/) | Escape-time Mandelbrot and Julia set rendering with smooth coloring — proven via hand-derived closed-form facts (exact periodic orbits, the main-cardioid/period-2-bulb membership formulas, conjugate symmetry) rather than a reference implementation, which surfaced a genuine floating-point chaos limit: `z→z²` on the unit circle is a textbook chaotic map, and double precision can't track it much past ~50 iterations. |

More things get added over time — new projects, or expansions of existing
ones.

## Running the tests

Each thing has its own test suite and its own `pyproject.toml`/pythonpath
config, meant to be run from inside that thing's directory:

```bash
cd things/chess && pip install -r requirements.txt && python3 -m pytest
```

To run all of them at once:

```bash
./run_all_tests.sh
```

(This runs each in its own subprocess rather than one combined pytest
invocation — several things share test file basenames like
`test_render.py`, and these are deliberately independent projects, not
one big package.)
