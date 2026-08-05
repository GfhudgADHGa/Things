"""Save/load a Game to/from JSON."""
from __future__ import annotations

import json
from typing import Any, Dict

from .dungeon import Dungeon
from .entities import Monster, Player
from .game import Game
from .geometry import Point, Rect
from .items import Item


def _point_to_list(p: Point):
    return [p.x, p.y]


def _point_from_list(lst) -> Point:
    return Point(lst[0], lst[1])


def _item_to_dict(item: Item) -> Dict[str, Any]:
    return dict(
        name=item.name,
        char=item.char,
        kind=item.kind,
        power=item.power,
        description=item.description,
    )


def _item_from_dict(d: Dict[str, Any]) -> Item:
    return Item(**d)


def _rect_to_list(r: Rect):
    return [r.x1, r.y1, r.x2, r.y2]


def _rect_from_list(lst) -> Rect:
    return Rect(*lst)


def to_dict(game: Game) -> Dict[str, Any]:
    dungeon = game.dungeon
    player = game.player

    return {
        "seed": game.seed,
        "width": game.width,
        "height": game.height,
        "depth": game.depth,
        "turn_count": game.turn_count,
        "game_over": game.game_over,
        "victory": game.victory,
        "messages": game.messages[-50:],
        "dungeon": {
            "tiles": ["".join(row) for row in dungeon.tiles],
            "rooms": [_rect_to_list(r) for r in dungeon.rooms],
            "stairs_up": _point_to_list(dungeon.stairs_up),
            "stairs_down": _point_to_list(dungeon.stairs_down),
        },
        "explored": [_point_to_list(p) for p in game.explored],
        "player": {
            "position": _point_to_list(player.position),
            "hp": player.hp,
            "max_hp": player.max_hp,
            "attack": player.attack,
            "defense": player.defense,
            "gold": player.gold,
            "level": player.level,
            "xp": player.xp,
            "xp_to_next": player.xp_to_next,
            "inventory": [_item_to_dict(i) for i in player.inventory],
            "equipped_weapon": _item_to_dict(player.equipped_weapon)
            if player.equipped_weapon
            else None,
            "equipped_armor": _item_to_dict(player.equipped_armor)
            if player.equipped_armor
            else None,
        },
        "monsters": [
            {
                "name": m.name,
                "char": m.char,
                "position": _point_to_list(m.position),
                "hp": m.hp,
                "max_hp": m.max_hp,
                "attack": m.attack,
                "defense": m.defense,
                "xp_reward": m.xp_reward,
                "kind": m.kind,
                "aggro": m.aggro,
            }
            for m in game.monsters
            if m.is_alive
        ],
        "items_on_floor": [
            {"position": _point_to_list(p), "item": _item_to_dict(item)}
            for p, item in game.items_on_floor.items()
        ],
    }


def from_dict(data: Dict[str, Any]) -> Game:
    d = data["dungeon"]
    dungeon = Dungeon(
        width=data["width"],
        height=data["height"],
        tiles=[list(row) for row in d["tiles"]],
        rooms=[_rect_from_list(r) for r in d["rooms"]],
        stairs_up=_point_from_list(d["stairs_up"]),
        stairs_down=_point_from_list(d["stairs_down"]),
    )

    p = data["player"]
    player = Player(
        name="Player",
        char="@",
        position=_point_from_list(p["position"]),
        hp=p["hp"],
        max_hp=p["max_hp"],
        attack=p["attack"],
        defense=p["defense"],
        gold=p["gold"],
        level=p["level"],
        xp=p["xp"],
        xp_to_next=p["xp_to_next"],
        inventory=[_item_from_dict(i) for i in p["inventory"]],
        equipped_weapon=_item_from_dict(p["equipped_weapon"]) if p["equipped_weapon"] else None,
        equipped_armor=_item_from_dict(p["equipped_armor"]) if p["equipped_armor"] else None,
    )

    monsters = [
        Monster(
            name=m["name"],
            char=m["char"],
            position=_point_from_list(m["position"]),
            hp=m["hp"],
            max_hp=m["max_hp"],
            attack=m["attack"],
            defense=m["defense"],
            xp_reward=m["xp_reward"],
            kind=m["kind"],
            aggro=m["aggro"],
        )
        for m in data["monsters"]
    ]

    items_on_floor = {
        _point_from_list(entry["position"]): _item_from_dict(entry["item"])
        for entry in data["items_on_floor"]
    }

    game = Game(
        seed=data["seed"],
        width=data["width"],
        height=data["height"],
        depth=data["depth"],
        dungeon=dungeon,
        player=player,
        monsters=monsters,
        items_on_floor=items_on_floor,
        explored={_point_from_list(p) for p in data["explored"]},
        messages=data["messages"],
        turn_count=data["turn_count"],
        game_over=data["game_over"],
        victory=data["victory"],
    )
    return game


def save_game(game: Game, path: str) -> None:
    with open(path, "w") as f:
        json.dump(to_dict(game), f)


def load_game(path: str) -> Game:
    with open(path) as f:
        data = json.load(f)
    return from_dict(data)
