from physics2d.body import Circle
from physics2d.vec2 import Vec2


def test_inverse_mass():
    c = Circle(Vec2(0, 0), Vec2(0, 0), radius=5, mass=2.0)
    assert c.inverse_mass == 0.5


def test_static_body_has_zero_inverse_mass():
    c = Circle(Vec2(0, 0), Vec2(0, 0), radius=5, mass=100.0, static=True)
    assert c.inverse_mass == 0.0


def test_default_color_and_restitution():
    c = Circle(Vec2(0, 0), Vec2(0, 0), radius=5)
    assert c.restitution == 0.8
    assert len(c.color) == 3
