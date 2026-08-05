"""Player and monster entities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .geometry import Point
from .items import Item


@dataclass
class Entity:
    name: str
    char: str
    position: Point
    hp: int
    max_hp: int
    attack: int
    defense: int

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> None:
        self.hp = max(0, self.hp - amount)

    def heal(self, amount: int) -> None:
        self.hp = min(self.max_hp, self.hp + amount)


@dataclass
class Monster(Entity):
    xp_reward: int = 5
    kind: str = "monster"
    aggro: bool = False


@dataclass
class Player(Entity):
    inventory: List[Item] = field(default_factory=list)
    equipped_weapon: Optional[Item] = None
    equipped_armor: Optional[Item] = None
    gold: int = 0
    level: int = 1
    xp: int = 0
    xp_to_next: int = 20
    inventory_capacity: int = 12

    @property
    def total_attack(self) -> int:
        bonus = self.equipped_weapon.power if self.equipped_weapon else 0
        return self.attack + bonus

    @property
    def total_defense(self) -> int:
        bonus = self.equipped_armor.power if self.equipped_armor else 0
        return self.defense + bonus

    def gain_xp(self, amount: int) -> bool:
        """Returns True if this brought about a level-up."""
        self.xp += amount
        leveled_up = False
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.5)
            self.max_hp += 10
            self.hp = self.max_hp
            self.attack += 2
            self.defense += 1
            leveled_up = True
        return leveled_up


MONSTER_TEMPLATES = {
    "rat": dict(char="r", hp=6, attack=2, defense=0, xp_reward=3),
    "goblin": dict(char="g", hp=12, attack=4, defense=1, xp_reward=6),
    "orc": dict(char="o", hp=20, attack=6, defense=2, xp_reward=12),
    "troll": dict(char="T", hp=35, attack=9, defense=3, xp_reward=25),
}


def make_monster(kind: str, position: Point, depth: int = 1) -> Monster:
    template = MONSTER_TEMPLATES[kind]
    depth_scale = 1.0 + 0.15 * (depth - 1)
    return Monster(
        name=kind.capitalize(),
        char=template["char"],
        position=position,
        hp=int(template["hp"] * depth_scale),
        max_hp=int(template["hp"] * depth_scale),
        attack=int(template["attack"] * depth_scale),
        defense=template["defense"],
        xp_reward=int(template["xp_reward"] * depth_scale),
        kind=kind,
    )


def make_player(position: Point) -> Player:
    return Player(
        name="Player",
        char="@",
        position=position,
        hp=30,
        max_hp=30,
        attack=5,
        defense=1,
    )
