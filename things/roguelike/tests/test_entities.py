from roguelike.entities import make_monster, make_player
from roguelike.geometry import Point
from roguelike.items import make_item


def test_make_player_defaults():
    p = make_player(Point(1, 1))
    assert p.is_alive
    assert p.hp == p.max_hp
    assert p.inventory == []
    assert p.equipped_weapon is None


def test_player_total_attack_and_defense_without_gear():
    p = make_player(Point(0, 0))
    assert p.total_attack == p.attack
    assert p.total_defense == p.defense


def test_player_total_attack_with_weapon():
    p = make_player(Point(0, 0))
    p.equipped_weapon = make_item("sword")
    assert p.total_attack == p.attack + 5


def test_player_total_defense_with_armor():
    p = make_player(Point(0, 0))
    p.equipped_armor = make_item("leather_armor")
    assert p.total_defense == p.defense + 2


def test_take_damage_and_heal_clamped():
    p = make_player(Point(0, 0))
    p.take_damage(p.max_hp + 100)
    assert p.hp == 0
    assert not p.is_alive
    p.heal(1000)
    assert p.hp == p.max_hp  # heal past max_hp is clamped, even after "death"


def test_gain_xp_levels_up_and_carries_remainder():
    p = make_player(Point(0, 0))
    original_max_hp = p.max_hp
    leveled = p.gain_xp(p.xp_to_next + 5)
    assert leveled
    assert p.level == 2
    assert p.xp == 5
    assert p.max_hp > original_max_hp
    assert p.hp == p.max_hp  # level-up fully heals


def test_gain_xp_without_enough_does_not_level():
    p = make_player(Point(0, 0))
    leveled = p.gain_xp(1)
    assert not leveled
    assert p.level == 1


def test_make_monster_scales_with_depth():
    shallow = make_monster("goblin", Point(0, 0), depth=1)
    deep = make_monster("goblin", Point(0, 0), depth=10)
    assert deep.max_hp > shallow.max_hp
    assert deep.attack > shallow.attack
