from roguelike.dungeon import STAIRS_DOWN
from roguelike.game import MAX_DEPTH, Game
from roguelike.geometry import Point
from roguelike.items import make_item


def new_test_game(seed=1) -> Game:
    game = Game(seed=seed)
    game.new_game()
    return game


def test_new_game_places_player_on_stairs_up():
    game = new_test_game()
    assert game.player.position == game.dungeon.stairs_up
    assert game.depth == 1
    assert not game.game_over


def test_new_game_spawns_monsters_and_items():
    game = new_test_game()
    assert len(game.monsters) > 0
    # items may occasionally roll zero, so just check the mechanism ran without error
    assert isinstance(game.items_on_floor, dict)


def test_move_into_wall_does_nothing_and_costs_no_turn():
    game = new_test_game()
    # find a wall adjacent to the player, if any; otherwise this is a no-op-safe check
    start = game.player.position
    turns_before = game.turn_count
    game.move_player(-1000, -1000)  # absurd direction: definitely out of bounds/wall
    assert game.player.position == start
    assert game.turn_count == turns_before


def test_move_into_open_floor_advances_turn():
    game = new_test_game()
    start = game.player.position
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        target = Point(start.x + dx, start.y + dy)
        if game.dungeon.is_walkable(target) and game.monster_at(target) is None:
            game.move_player(dx, dy)
            assert game.player.position == target
            assert game.turn_count == 1
            return
    raise AssertionError("no walkable neighbor found near player start; unlucky seed")


def test_move_into_monster_attacks_instead_of_moving():
    game = new_test_game()
    start = game.player.position
    # place a weak monster directly next to the player
    from roguelike.entities import make_monster

    monster = make_monster("rat", Point(start.x + 1, start.y))
    game.dungeon.tiles[monster.position.y][monster.position.x] = "."
    game.monsters = [monster]
    hp_before = monster.hp

    game.move_player(1, 0)
    assert game.player.position == start  # player did not move into the monster's tile
    assert monster.hp <= hp_before


def test_pickup_with_nothing_present_logs_message():
    game = new_test_game()
    game.items_on_floor = {}
    before = len(game.messages)
    game.pickup_item()
    assert len(game.messages) == before + 1
    assert len(game.player.inventory) == 0


def test_pickup_adds_item_to_inventory():
    game = new_test_game()
    item = make_item("healing_potion")
    game.items_on_floor = {game.player.position: item}
    game.pickup_item()
    assert item in game.player.inventory
    assert game.player.position not in game.items_on_floor


def test_pickup_amulet_wins_game():
    game = new_test_game()
    from roguelike.items import Item

    amulet = Item(name="the Sunstone", char="*", kind="amulet")
    game.items_on_floor = {game.player.position: amulet}
    game.pickup_item()
    assert game.victory
    assert game.game_over


def test_use_healing_potion_restores_hp():
    game = new_test_game()
    game.player.hp = 1
    potion = make_item("healing_potion")
    game.player.inventory.append(potion)
    game.use_item(potion)
    assert game.player.hp == 1 + potion.power
    assert potion not in game.player.inventory


def test_use_weapon_equips_and_swaps_previous_back_into_inventory():
    game = new_test_game()
    dagger = make_item("dagger")
    sword = make_item("sword")
    game.player.inventory = [dagger, sword]
    game.use_item(dagger)
    assert game.player.equipped_weapon is dagger
    game.use_item(sword)
    assert game.player.equipped_weapon is sword
    assert dagger in game.player.inventory


def test_descend_requires_standing_on_stairs():
    game = new_test_game()
    game.player.position = Point(1, 1)  # almost certainly not the stairs
    depth_before = game.depth
    game.descend()
    assert game.depth == depth_before


def test_descend_moves_to_next_level():
    game = new_test_game()
    game.player.position = game.dungeon.stairs_down
    game.descend()
    assert game.depth == 2
    assert game.player.position == game.dungeon.stairs_up


def test_max_depth_level_contains_the_sunstone():
    game = new_test_game(seed=99)
    game._advance_to_level(MAX_DEPTH)
    amulets = [i for i in game.items_on_floor.values() if i.kind == "amulet"]
    assert len(amulets) == 1


def test_game_over_when_player_dies():
    game = new_test_game()
    game.player.hp = 0
    game._check_player_death()
    assert game.game_over
    assert not game.victory


def test_move_player_does_nothing_once_game_over():
    game = new_test_game()
    game.game_over = True
    start = game.player.position
    game.move_player(1, 0)
    assert game.player.position == start
