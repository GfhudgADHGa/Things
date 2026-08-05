# roguelike

A terminal dungeon crawler in the classic mold: procedurally generated
levels, permadeath, turn-based bump-to-attack combat, and a fog of war.
Find the **Sunstone** on dungeon level 10 to win.

Game logic is fully decoupled from the terminal UI — everything in
`roguelike/game.py` and friends is plain Python with no I/O, so it's
exercised by a real test suite. `roguelike/ui_curses.py` is a thin `curses`
renderer on top.

## Play

```bash
python3 main.py               # new game
python3 main.py --seed 42     # new game with a specific dungeon seed
python3 main.py --load        # resume from savegame.json, if present
```

Requires a real terminal (curses needs a TTY) at least ~80x28.

### Controls

| Key | Action |
|---|---|
| `h` `j` `k` `l` or arrow keys | move west / south / north / east |
| `y` `u` `b` `n` | move diagonally (NW / NE / SW / SE) |
| walking into a monster | attack it |
| `g` | pick up whatever is on your tile |
| `i` | open inventory — press a letter to use/equip/drink/read that item |
| `>` | descend stairs (must be standing on them) |
| `s` | save to `savegame.json` |
| `?` | help |
| `q` | quit |

## How it works

```
roguelike/
  geometry.py     Point, Rect
  dungeon.py       procedural room+corridor generation (seeded)
  fov.py            Bresenham-line-of-sight field of view
  entities.py      Player / Monster stats, leveling, monster templates
  items.py          potions, scrolls, weapons, armor
  combat.py        attack resolution (damage = attack - defense ± variance, min 1)
  ai.py              monster chase/wander behavior
  game.py           the turn loop: ties everything together, no I/O
  save.py            JSON (de)serialization of a Game
  ui_curses.py      curses rendering + input loop
```

**Dungeon generation** places rooms at random non-overlapping positions and
connects each new room to the previous one with an L-shaped corridor, so the
whole level is guaranteed reachable from the start. Stairs up sit in the
first room, stairs down in the last.

**Field of view** casts a Bresenham line from the player (or a monster) to
every tile within its sight radius; a tile is visible if nothing but open
floor lies between it and the origin. Explored-but-not-currently-visible
tiles are remembered and drawn dim (classic fog of war).

**Combat** is a simple bump: walking into an occupied tile attacks instead
of moving. Damage is `attacker.total_attack - defender.total_defense + random
variance`, floored at 1, so a fight is never a true stalemate.

**Monsters** are idle until the player enters their field of view, at which
point they become permanently aggro'd and path toward the player one tile at
a time (8-directional greedy pathing — not A*, but effective on these small,
open, single-corridor-dominant levels).

**Progression**: monster stats scale up with dungeon depth (deeper rats hit
harder than shallow ones), and the player levels up on enough XP, gaining
max HP, attack, and defense.

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

62 tests cover dungeon generation (determinism, connectivity via flood
fill, stairs placement), FOV (line tracing, radius limits, wall occlusion),
combat math, entity leveling, item templates, monster AI (wander vs. chase
vs. attack), the full game turn loop (movement, combat, pickup, equip,
descending, win/lose conditions), and save/load round-tripping. The curses
UI itself isn't unit tested (no TTY in CI) — it was verified manually by
driving it inside a `tmux` session.

## Possible expansions

- A* pathing for smarter monster chasing around obstacles
- Ranged weapons / thrown items
- Traps, locked doors, keys
- A proper "return to town" loop with shops
- Multiple named unique monsters/bosses per depth tier
