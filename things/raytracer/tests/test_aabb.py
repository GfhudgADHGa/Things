from raytracer.aabb import AABB
from raytracer.ray import Ray
from raytracer.vec3 import Vec3


def unit_box():
    return AABB(Vec3(-1, -1, -1), Vec3(1, 1, 1))


def test_ray_through_center_hits():
    box = unit_box()
    ray = Ray(Vec3(0, 0, -5), Vec3(0, 0, 1))
    assert box.hit(ray, 0.001, float("inf"))


def test_ray_missing_box_entirely():
    box = unit_box()
    ray = Ray(Vec3(5, 5, -5), Vec3(0, 0, 1))
    assert not box.hit(ray, 0.001, float("inf"))


def test_ray_pointing_away_from_box_misses():
    box = unit_box()
    ray = Ray(Vec3(0, 0, -5), Vec3(0, 0, -1))
    assert not box.hit(ray, 0.001, float("inf"))


def test_ray_along_axis_aligned_direction():
    box = unit_box()
    ray = Ray(Vec3(-5, 0, 0), Vec3(1, 0, 0))
    assert box.hit(ray, 0.001, float("inf"))


def test_ray_grazing_edge_misses_when_offset_beyond():
    box = unit_box()
    ray = Ray(Vec3(0, 1.5, -5), Vec3(0, 0, 1))
    assert not box.hit(ray, 0.001, float("inf"))


def test_t_range_restricts_hit():
    box = AABB(Vec3(-1, -1, 9), Vec3(1, 1, 11))
    ray = Ray(Vec3(0, 0, 0), Vec3(0, 0, 1))
    assert box.hit(ray, 0.001, float("inf"))
    assert not box.hit(ray, 0.001, 5.0)  # box is beyond t_max


def test_surrounding_box_encloses_both():
    a = AABB(Vec3(0, 0, 0), Vec3(1, 1, 1))
    b = AABB(Vec3(-2, 5, -3), Vec3(-1, 6, -2))
    combined = AABB.surrounding(a, b)
    assert combined.minimum == Vec3(-2, 0, -3)
    assert combined.maximum == Vec3(1, 6, 1)


def test_origin_inside_box_hits():
    box = unit_box()
    ray = Ray(Vec3(0, 0, 0), Vec3(1, 0, 0))
    assert box.hit(ray, 0.001, float("inf"))
