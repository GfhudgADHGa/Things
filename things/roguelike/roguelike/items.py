"""Items: potions, scrolls, weapons, armor, gold."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Item:
    name: str
    char: str
    kind: str  # "potion", "scroll", "weapon", "armor"
    power: int = 0  # heal amount / attack bonus / defense bonus
    description: str = ""


ITEM_TEMPLATES = {
    "healing_potion": dict(
        name="Potion of Healing",
        char="!",
        kind="potion",
        power=15,
        description="Restores 15 HP.",
    ),
    "greater_healing_potion": dict(
        name="Potion of Greater Healing",
        char="!",
        kind="potion",
        power=30,
        description="Restores 30 HP.",
    ),
    "scroll_of_teleport": dict(
        name="Scroll of Teleportation",
        char="?",
        kind="scroll",
        power=0,
        description="Teleports you to a random spot on this floor.",
    ),
    "dagger": dict(
        name="Dagger",
        char="/",
        kind="weapon",
        power=2,
        description="+2 attack.",
    ),
    "sword": dict(
        name="Sword",
        char="/",
        kind="weapon",
        power=5,
        description="+5 attack.",
    ),
    "longsword": dict(
        name="Longsword",
        char="/",
        kind="weapon",
        power=8,
        description="+8 attack.",
    ),
    "leather_armor": dict(
        name="Leather Armor",
        char="[",
        kind="armor",
        power=2,
        description="+2 defense.",
    ),
    "chainmail": dict(
        name="Chainmail",
        char="[",
        kind="armor",
        power=5,
        description="+5 defense.",
    ),
}


def make_item(template_key: str) -> Item:
    return Item(**ITEM_TEMPLATES[template_key])
