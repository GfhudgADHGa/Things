import math

from raytracer.vec3 import Vec3, lerp


def test_add_sub_neg():
    a = Vec3(1, 2, 3)
    b = Vec3(4, 5, 6)
    assert a + b == Vec3(5, 7, 9)
    assert b - a == Vec3(3, 3, 3)
    assert -a == Vec3(-1, -2, -3)


def test_scalar_mul_div():
    a = Vec3(1, 2, 3)
    assert a * 2 == Vec3(2, 4, 6)
    assert 2 * a == Vec3(2, 4, 6)
    assert (a * 4) / 4 == a


def test_componentwise_mul():
    a = Vec3(1, 2, 3)
    b = Vec3(2, 2, 2)
    assert a * b == Vec3(2, 4, 6)


def test_dot():
    a = Vec3(1, 0, 0)
    b = Vec3(0, 1, 0)
    assert a.dot(b) == 0
    assert a.dot(a) == 1


def test_cross():
    x = Vec3(1, 0, 0)
    y = Vec3(0, 1, 0)
    z = Vec3(0, 0, 1)
    assert x.cross(y) == z
    assert y.cross(x) == -z


def test_length_and_normalize():
    a = Vec3(3, 4, 0)
    assert a.length() == 5
    n = a.normalized()
    assert math.isclose(n.length(), 1.0)
    assert math.isclose(n.x, 0.6) and math.isclose(n.y, 0.8) and n.z == 0.0


def test_reflect_off_flat_surface():
    incoming = Vec3(1, -1, 0)
    normal = Vec3(0, 1, 0)
    reflected = incoming.reflect(normal)
    assert reflected == Vec3(1, 1, 0)


def test_near_zero():
    assert Vec3(0, 0, 0).near_zero()
    assert Vec3(1e-10, -1e-10, 0).near_zero()
    assert not Vec3(0.1, 0, 0).near_zero()


def test_lerp_endpoints():
    a = Vec3(0, 0, 0)
    b = Vec3(1, 1, 1)
    assert lerp(a, b, 0.0) == a
    assert lerp(a, b, 1.0) == b
    assert lerp(a, b, 0.5) == Vec3(0.5, 0.5, 0.5)


def test_random_in_unit_sphere_is_bounded():
    for _ in range(200):
        p = Vec3.random_in_unit_sphere()
        assert p.length_squared() < 1


def test_random_unit_vector_has_unit_length():
    for _ in range(200):
        v = Vec3.random_unit_vector()
        assert math.isclose(v.length(), 1.0, rel_tol=1e-9)
