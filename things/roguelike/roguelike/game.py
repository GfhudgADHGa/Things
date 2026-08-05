"""Ties dungeon generation, entities, combat, items and AI into a playable game."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from . import ai
from .combat import resolve_attack
from .dungeon import STAIRS_DOWN, Dungeon, generate_dungeon
from .entities import Monster, Player, make_monster, make_player
from .fov import compute_fov
from .geometry import Point
from .items import Item, make_item

PLAYER_SIGHT_RADIUS = 8
MONSTER_SIGHT_RADIUS = 6
MAX_DEPTH = 10

MONSTER_POOL_BY_DEPTH = [
    (1, ["rat", "rat", "goblin"]),
    (3, ["rat", "goblin", "goblin", "orc"]),
    (6, ["goblin", "orc", "orc", "troll"]),
    (9, ["orc", "troll", "troll"]),
]

ITEM_POOL = [
    "healing_potion",
    "healing_potion",
    "scroll_of_teleport",
    "dagger",
    "sword",
    "leather_armor",
]


def _monster_pool_for_depth(depth: int) -> List[str]:
    pool = MONSTER_POOL_BY_DEPTH[0][1]
    for min_depth, candidates in MONSTER_POOL_BY_DEPTH:
        if depth >= min_depth:
            pool = candidates
    return pool


@dataclass
class Game:
    seed: int = field(default_factory=lambda: random.randrange(1_000_000))
    width: int = 70
    height: int = 20
    depth: int = 0
    dungeon: Optional[Dungeon] = None
    player: Optional[Player] = None
    monsters: List[Monster] = field(default_factory=list)
    items_on_floor: Dict[Point, Item] = field(default_factory=dict)
    explored: Set[Point] = field(default_factory=set)
    messages: List[str] = field(default_factory=list)
    turn_count: int = 0
    game_over: bool = False
    victory: bool = False
    rng: random.Random = field(default=None)

    def __post_init__(self):
        if self.rng is None:
            self.rng = random.Random(self.seed)

    def log(self, message: str) -> None:
        self.messages.append(message)
        if len(self.messages) > 200:
            self.messages = self.messages[-200:]

    def new_game(self) -> None:
        self.depth = 0
        self._advance_to_level(1)
        self.log("You descend into the dungeon.")

    def _advance_to_level(self, depth: int) -> None:
        self.depth = depth
        level_seed = self.seed * 1000 + depth
        self.dungeon = generate_dungeon(self.width, self.height, level_seed)
        self.explored = set()
        self.monsters = []
        self.items_on_floor = {}

        start = self.dungeon.stairs_up
        if self.player is None:
            self.player = make_player(start)
        else:
            self.player.position = start

        self._populate_level(level_seed)

    def _populate_level(self, level_seed: int) -> None:
        rng = random.Random(level_seed + 1)
        floor_tiles = [
            p
            for room in self.dungeon.rooms[1:]
            for p in room.interior_points()
            if self.dungeon.is_walkable(p)
        ]
        if not floor_tiles:
            floor_tiles = [self.dungeon.stairs_down]

        n_monsters = min(len(floor_tiles), rng.randint(3, 6) + self.depth // 2)
        pool = _monster_pool_for_depth(self.depth)
        monster_spots = rng.sample(floor_tiles, n_monsters) if floor_tiles else []
        for spot in monster_spots:
            kind = rng.choice(pool)
            self.monsters.append(make_monster(kind, spot, self.depth))

        remaining = [p for p in floor_tiles if p not in monster_spots]
        n_items = min(len(remaining), rng.randint(2, 5))
        item_spots = rng.sample(remaining, n_items) if remaining else []
        for spot in item_spots:
            key = rng.choice(ITEM_POOL)
            self.items_on_floor[spot] = make_item(key)

        if self.depth == MAX_DEPTH and remaining:
            amulet_spot = rng.choice([p for p in remaining if p not in item_spots] or remaining)
            self.items_on_floor[amulet_spot] = Item(
                name="the Sunstone",
                char="*",
                kind="amulet",
                power=0,
                description="A warm, glowing stone. This is what you came for.",
            )

    def monster_at(self, point: Point) -> Optional[Monster]:
        for m in self.monsters:
            if m.is_alive and m.position == point:
                return m
        return None

    def visible_tiles(self) -> Set[Point]:
        visible = compute_fov(self.dungeon, self.player.position, PLAYER_SIGHT_RADIUS)
        self.explored |= visible
        return visible

    def move_player(self, dx: int, dy: int) -> None:
        if self.game_over:
            return

        target = Point(self.player.position.x + dx, self.player.position.y + dy)
        if not self.dungeon.is_walkable(target):
            return

        monster = self.monster_at(target)
        if monster is not None:
            result = resolve_attack(self.player, monster, self.rng)
            self.log(f"You hit the {result.defender_name} for {result.damage}.")
            if result.defender_died:
                self.log(f"The {result.defender_name} dies.")
                leveled_up = self.player.gain_xp(monster.xp_reward)
                if leveled_up:
                    self.log(f"You reach level {self.player.level}!")
        else:
            self.player.position = target

        self.turn_count += 1
        self._monsters_turn()
        self._check_player_death()

    def pickup_item(self) -> None:
        item = self.items_on_floor.get(self.player.position)
        if item is None:
            self.log("There is nothing here to pick up.")
            return
        if item.kind == "amulet":
            del self.items_on_floor[self.player.position]
            self.victory = True
            self.game_over = True
            self.log(f"You found {item.name}! You win!")
            return
        if len(self.player.inventory) >= self.player.inventory_capacity:
            self.log("Your inventory is full.")
            return
        del self.items_on_floor[self.player.position]
        self.player.inventory.append(item)
        self.log(f"You pick up {item.name}.")

    def use_item(self, item: Item) -> None:
        if item not in self.player.inventory:
            return
        if item.kind == "potion":
            self.player.heal(item.power)
            self.log(f"You drink {item.name} and recover {item.power} HP.")
            self.player.inventory.remove(item)
        elif item.kind == "scroll":
            floor_tiles = [
                p
                for room in self.dungeon.rooms
                for p in room.interior_points()
                if self.dungeon.is_walkable(p)
            ]
            if floor_tiles:
                self.player.position = self.rng.choice(floor_tiles)
                self.log(f"You read {item.name} and vanish in a puff of smoke.")
            self.player.inventory.remove(item)
        elif item.kind == "weapon":
            previous = self.player.equipped_weapon
            self.player.equipped_weapon = item
            self.player.inventory.remove(item)
            if previous is not None:
                self.player.inventory.append(previous)
            self.log(f"You wield {item.name}.")
        elif item.kind == "armor":
            previous = self.player.equipped_armor
            self.player.equipped_armor = item
            self.player.inventory.remove(item)
            if previous is not None:
                self.player.inventory.append(previous)
            self.log(f"You wear {item.name}.")

        self.turn_count += 1
        self._monsters_turn()
        self._check_player_death()

    def descend(self) -> None:
        if self.player.position != self.dungeon.stairs_down:
            self.log("There are no stairs down here.")
            return
        if self.depth >= MAX_DEPTH:
            self.log("This is the deepest level. Find the Sunstone!")
            return
        self._advance_to_level(self.depth + 1)
        self.log(f"You descend to level {self.depth}.")

    def _monsters_turn(self) -> None:
        if self.game_over:
            return
        occupied = {m.position for m in self.monsters if m.is_alive}
        occupied.add(self.player.position)

        for monster in self.monsters:
            if not monster.is_alive:
                continue
            monster_fov = compute_fov(self.dungeon, monster.position, MONSTER_SIGHT_RADIUS)
            move = ai.take_monster_turn(
                monster, self.dungeon, self.player, monster_fov, occupied, self.rng
            )
            if move is None:
                continue
            if move == self.player.position:
                result = resolve_attack(monster, self.player, self.rng)
                self.log(f"The {result.attacker_name} hits you for {result.damage}.")
                if result.defender_died:
                    self.game_over = True
                    self.log("You have died.")
                    return
            else:
                occupied.discard(monster.position)
                monster.position = move
                occupied.add(move)

    def _check_player_death(self) -> None:
        if not self.player.is_alive:
            self.game_over = True
            self.log("You have died.")
