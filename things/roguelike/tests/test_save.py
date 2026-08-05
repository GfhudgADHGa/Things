import os

from roguelike.game import Game
from roguelike.items import make_item
from roguelike.save import from_dict, load_game, save_game, to_dict


def make_populated_game() -> Game:
    game = Game(seed=7)
    game.new_game()
    game.player.inventory.append(make_item("healing_potion"))
    game.player.equipped_weapon = make_item("sword")
    game.player.gold = 42
    game.player.gain_xp(15)
    game.log("A test message.")
    return game


def test_roundtrip_preserves_player_state():
    game = make_populated_game()
    data = to_dict(game)
    restored = from_dict(data)

    assert restored.player.hp == game.player.hp
    assert restored.player.gold == 42
    assert restored.player.level == game.player.level
    assert restored.player.equipped_weapon.name == "Sword"
    assert len(restored.player.inventory) == 1
    assert restored.player.inventory[0].name == "Potion of Healing"


def test_roundtrip_preserves_dungeon_layout():
    game = make_populated_game()
    restored = from_dict(to_dict(game))
    assert restored.dungeon.tiles == game.dungeon.tiles
    assert restored.dungeon.stairs_down == game.dungeon.stairs_down
    assert restored.depth == game.depth


def test_roundtrip_preserves_monsters():
    game = make_populated_game()
    restored = from_dict(to_dict(game))
    assert len(restored.monsters) == len([m for m in game.monsters if m.is_alive])
    if restored.monsters:
        assert restored.monsters[0].kind == game.monsters[0].kind


def test_save_and_load_file_roundtrip(tmp_path):
    game = make_populated_game()
    path = str(tmp_path / "save.json")
    save_game(game, path)
    assert os.path.exists(path)

    loaded = load_game(path)
    assert loaded.player.hp == game.player.hp
    assert loaded.depth == game.depth
    assert loaded.messages[-1] == "A test message."
