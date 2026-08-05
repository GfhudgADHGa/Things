"""Attack resolution between two entities."""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class AttackResult:
    attacker_name: str
    defender_name: str
    damage: int
    defender_died: bool


def resolve_attack(attacker, defender, rng: random.Random | None = None) -> AttackResult:
    rng = rng or random
    attack_power = attacker.total_attack if hasattr(attacker, "total_attack") else attacker.attack
    defense_power = defender.total_defense if hasattr(defender, "total_defense") else defender.defense

    variance = rng.randint(-1, 2)
    raw_damage = attack_power + variance - defense_power
    damage = max(1, raw_damage)

    defender.take_damage(damage)
    return AttackResult(
        attacker_name=attacker.name,
        defender_name=defender.name,
        damage=damage,
        defender_died=not defender.is_alive,
    )
