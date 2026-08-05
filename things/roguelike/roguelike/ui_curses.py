"""Curses front-end. Not covered by the automated test suite (no TTY in CI);
game logic itself lives in game.py and is fully tested there.
"""
from __future__ import annotations

import curses
import os

from .dungeon import STAIRS_DOWN, STAIRS_UP, WALL
from .game import MAX_DEPTH, Game
from .geometry import Point
from .save import load_game, save_game

SAVE_PATH = os.path.join(os.path.dirname(__file__), "..", "savegame.json")

MOVE_KEYS = {
    ord("h"): (-1, 0),
    ord("l"): (1, 0),
    ord("k"): (0, -1),
    ord("j"): (0, 1),
    ord("y"): (-1, -1),
    ord("u"): (1, -1),
    ord("b"): (-1, 1),
    ord("n"): (1, 1),
    curses.KEY_LEFT: (-1, 0),
    curses.KEY_RIGHT: (1, 0),
    curses.KEY_UP: (0, -1),
    curses.KEY_DOWN: (0, 1),
}

COLOR_WALL = 1
COLOR_FLOOR = 2
COLOR_PLAYER = 3
COLOR_MONSTER = 4
COLOR_ITEM = 5
COLOR_STAIRS = 6
COLOR_HUD = 7
COLOR_EXPLORED = 8


def _init_colors() -> None:
    if not curses.has_colors():
        return
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOR_WALL, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_FLOOR, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_PLAYER, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_MONSTER, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_ITEM, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOR_STAIRS, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_HUD, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_EXPLORED, curses.COLOR_BLUE, -1)


def _safe_addstr(win, y, x, text, attr=0) -> None:
    max_y, max_x = win.getmaxyx()
    if y < 0 or y >= max_y or x >= max_x:
        return
    text = text[: max(0, max_x - x - 1)]
    try:
        win.addstr(y, x, text, attr)
    except curses.error:
        pass


def draw(win, game: Game) -> None:
    win.erase()
    visible = game.visible_tiles()
    dungeon = game.dungeon

    for y in range(dungeon.height):
        for x in range(dungeon.width):
            p = Point(x, y)
            if p in visible:
                ch = dungeon.tile_at(p)
                color = {
                    WALL: COLOR_WALL,
                    STAIRS_DOWN: COLOR_STAIRS,
                    STAIRS_UP: COLOR_STAIRS,
                }.get(ch, COLOR_FLOOR)
                _safe_addstr(win, y + 1, x, ch, curses.color_pair(color))
            elif p in game.explored:
                ch = dungeon.tile_at(p)
                _safe_addstr(win, y + 1, x, ch, curses.color_pair(COLOR_EXPLORED) | curses.A_DIM)

    for point, item in game.items_on_floor.items():
        if point in visible:
            _safe_addstr(win, point.y + 1, point.x, item.char, curses.color_pair(COLOR_ITEM))

    for monster in game.monsters:
        if monster.is_alive and monster.position in visible:
            _safe_addstr(
                win, monster.position.y + 1, monster.position.x, monster.char,
                curses.color_pair(COLOR_MONSTER) | curses.A_BOLD,
            )

    p = game.player.position
    _safe_addstr(win, p.y + 1, p.x, "@", curses.color_pair(COLOR_PLAYER) | curses.A_BOLD)

    hud = (
        f"HP {game.player.hp}/{game.player.max_hp}  "
        f"Lv {game.player.level} (xp {game.player.xp}/{game.player.xp_to_next})  "
        f"Atk {game.player.total_attack} Def {game.player.total_defense}  "
        f"Depth {game.depth}/{MAX_DEPTH}  Turn {game.turn_count}"
    )
    _safe_addstr(win, 0, 0, hud, curses.color_pair(COLOR_HUD) | curses.A_BOLD)

    for i, message in enumerate(game.messages[-3:]):
        _safe_addstr(win, dungeon.height + 2 + i, 0, message, curses.color_pair(COLOR_HUD))

    help_line = "hjkl/arrows: move  g: pickup  i: inventory  >: descend  s: save  q: quit  ?: help"
    _safe_addstr(win, dungeon.height + 6, 0, help_line, curses.A_DIM)

    win.refresh()


def show_inventory(win, game: Game) -> None:
    win.erase()
    _safe_addstr(win, 0, 0, "Inventory (select a letter to use/equip, any other key to close)", curses.A_BOLD)
    if not game.player.inventory:
        _safe_addstr(win, 2, 0, "(empty)")
    for i, item in enumerate(game.player.inventory):
        letter = chr(ord("a") + i)
        equipped = ""
        if item is game.player.equipped_weapon or item is game.player.equipped_armor:
            equipped = " (equipped)"
        _safe_addstr(win, 2 + i, 0, f"{letter}) {item.name} - {item.description}{equipped}")
    win.refresh()

    key = win.getch()
    index = key - ord("a")
    if 0 <= index < len(game.player.inventory):
        game.use_item(game.player.inventory[index])


def show_help(win) -> None:
    win.erase()
    lines = [
        "Movement: h/j/k/l or arrow keys (west/south/north/east)",
        "          y/u/b/n for diagonals",
        "g : pick up item on the floor",
        "i : open inventory (potions heal, scrolls teleport,",
        "    weapons/armor equip automatically)",
        "> : descend stairs (must be standing on them)",
        "s : save game",
        "q : quit",
        "",
        "Find the Sunstone on the deepest level to win.",
        "",
        "Press any key to continue...",
    ]
    for i, line in enumerate(lines):
        _safe_addstr(win, i, 0, line)
    win.refresh()
    win.getch()


def show_end_screen(win, game: Game) -> None:
    win.erase()
    if game.victory:
        _safe_addstr(win, 1, 0, "You escaped with the Sunstone. You win!", curses.A_BOLD)
    else:
        _safe_addstr(win, 1, 0, "You have died.", curses.A_BOLD)
    _safe_addstr(win, 3, 0, f"Reached depth {game.depth}, level {game.player.level}, turn {game.turn_count}.")
    _safe_addstr(win, 5, 0, "Press any key to exit...")
    win.refresh()
    win.getch()


def run(stdscr, game: Game) -> None:
    curses.curs_set(0)
    _init_colors()
    stdscr.keypad(True)

    while not game.game_over:
        draw(stdscr, game)
        key = stdscr.getch()

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            game.move_player(dx, dy)
        elif key == ord("g"):
            game.pickup_item()
        elif key == ord("i"):
            show_inventory(stdscr, game)
        elif key == ord(">"):
            game.descend()
        elif key == ord("s"):
            save_game(game, SAVE_PATH)
            game.log("Game saved.")
        elif key == ord("?"):
            show_help(stdscr)
        elif key == ord("q"):
            break

    if game.game_over:
        show_end_screen(stdscr, game)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="A terminal roguelike.")
    parser.add_argument("--load", action="store_true", help="load savegame.json if present")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    if args.load and os.path.exists(SAVE_PATH):
        game = load_game(SAVE_PATH)
    else:
        game = Game(seed=args.seed) if args.seed is not None else Game()
        game.new_game()

    curses.wrapper(run, game)
