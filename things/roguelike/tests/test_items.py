from roguelike.items import ITEM_TEMPLATES, make_item


def test_make_item_from_every_template():
    for key in ITEM_TEMPLATES:
        item = make_item(key)
        assert item.name
        assert item.char
        assert item.kind in {"potion", "scroll", "weapon", "armor"}


def test_make_item_returns_independent_instances():
    a = make_item("healing_potion")
    b = make_item("healing_potion")
    assert a is not b
    a.power = 999
    assert b.power != 999
