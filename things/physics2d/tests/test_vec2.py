import math

from physics2d.vec2 import Vec2


def test_add_sub():
    a = Vec2(1, 2)
    b = Vec2(3, 4)
    assert a + b == Vec2(4, 6)
    assert b - a == Vec2(2, 2)


def test_neg():
    assert -Vec2(1, -2) == Vec2(-1, 2)


def test_scalar_mul():
    assert Vec2(2, 3) * 2 == Vec2(4, 6)
    assert 2 * Vec2(2, 3) == Vec2(4, 6)


def test_dot():
    assert Vec2(1, 0).dot(Vec2(0, 1)) == 0
    assert Vec2(2, 3).dot(Vec2(4, 5)) == 23


def test_length():
    assert Vec2(3, 4).length() == 5


def test_normalized():
    n = Vec2(3, 4).normalized()
    assert math.isclose(n.length(), 1.0)
    assert n == Vec2(0.6, 0.8)


def test_normalized_zero_vector_is_zero():
    assert Vec2(0, 0).normalized() == Vec2(0, 0)
