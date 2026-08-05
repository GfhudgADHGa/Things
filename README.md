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
| [`roguelike`](things/roguelike/) | A terminal dungeon crawler: procedural levels, fog of war, turn-based combat, leveling, save/load. Playable with `curses`. |
| [`pebble`](things/pebble/) | A small scripting language, implemented from scratch: hand-written lexer, recursive-descent parser, tree-walking interpreter with closures. |
| [`chess`](things/chess/) | A chess engine: full legal move generation (verified against known perft values), alpha-beta search, playable from the terminal. |
| [`regex`](things/regex/) | A regex engine built on Thompson NFA construction — no backtracking, so it's immune to catastrophic ReDoS blowup (verified against Python's `re`, which isn't). |
| [`kvstore`](things/kvstore/) | A durable key-value store: fsync'd write-ahead log, crash-safe recovery (verified by literally corrupting the log file and checking recovery), atomic compaction. |
| [`procmusic`](things/procmusic/) | Algorithmic music generation from scratch: raw waveform synthesis, a hand-rolled WAV writer, music theory (scales/chords), and a small composer. Produces actual playable songs. |
| [`physics2d`](things/physics2d/) | A 2D rigid-body physics simulation (gravity, elastic collisions) rendered to an animated GIF via a from-scratch LZW encoder — including a real encoder/decoder sync bug found and fixed using Pillow as a decode oracle. |

More things get added over time — new projects, or expansions of existing
ones.
