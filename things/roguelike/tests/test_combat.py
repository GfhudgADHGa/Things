import random

from roguelike.combat import resolve_attack
from roguelike.entities import make_monster, make_player
from roguelike.geometry import Point


def test_resolve_attack_deals_at_least_one_damage():
    rng = random.Random(0)
    attacker = make_player(Point(0, 0))
    defender = make_monster("troll", Point(1, 0), depth=1)
    # give defender absurd defense to try to force the min-1-damage floor
    defender.defense = 999
    result = resolve_attack(attacker, defender, rng)
    assert result.damage >= 1


def test_resolve_attack_reduces_defender_hp():
    rng = random.Random(1)
    attacker = make_player(Point(0, 0))
    defender = make_monster("rat", Point(1, 0), depth=1)
    hp_before = defender.hp
    result = resolve_attack(attacker, defender, rng)
    assert defender.hp == hp_before - result.damage


def test_resolve_attack_reports_death():
    rng = random.Random(2)
    attacker = make_player(Point(0, 0))
    attacker.attack = 999
    defender = make_monster("rat", Point(1, 0), depth=1)
    result = resolve_attack(attacker, defender, rng)
    assert result.defender_died
    assert not defender.is_alive


def test_resolve_attack_uses_equipped_weapon_bonus():
    from roguelike.items import make_item

    rng_a = random.Random(3)
    rng_b = random.Random(3)
    weak = make_player(Point(0, 0))
    strong = make_player(Point(0, 0))
    strong.equipped_weapon = make_item("longsword")

    target_a = make_monster("troll", Point(1, 0), depth=1)
    target_b = make_monster("troll", Point(1, 0), depth=1)

    result_a = resolve_attack(weak, target_a, rng_a)
    result_b = resolve_attack(strong, target_b, rng_b)
    assert result_b.damage > result_a.damage


def test_resolve_attack_is_deterministic_given_rng_seed():
    r1 = resolve_attack(
        make_player(Point(0, 0)), make_monster("orc", Point(1, 0)), random.Random(123)
    )
    r2 = resolve_attack(
        make_player(Point(0, 0)), make_monster("orc", Point(1, 0)), random.Random(123)
    )
    assert r1.damage == r2.damage
