import math

from raytracer.hittable import HittableList, Plane, Sphere
from raytracer.materials import Lambertian
from raytracer.ray import Ray
from raytracer.vec3 import Vec3


def make_material():
    return Lambertian(Vec3(0.5, 0.5, 0.5))


def test_sphere_hit_along_axis():
    sphere = Sphere(Vec3(0, 0, -1), 0.5, make_material())
    ray = Ray(Vec3(0, 0, 0), Vec3(0, 0, -1))
    rec = sphere.hit(ray, 0.001, float("inf"))
    assert rec is not None
    assert math.isclose(rec.t, 0.5)
    assert rec.point == Vec3(0, 0, -0.5)
    assert rec.normal == Vec3(0, 0, 1)
    assert rec.front_face is True


def test_sphere_miss():
    sphere = Sphere(Vec3(0, 0, -1), 0.5, make_material())
    ray = Ray(Vec3(0, 5, 0), Vec3(0, 0, -1))
    assert sphere.hit(ray, 0.001, float("inf")) is None


def test_sphere_hit_from_inside_has_back_face():
    sphere = Sphere(Vec3(0, 0, 0), 1.0, make_material())
    ray = Ray(Vec3(0, 0, 0), Vec3(0, 0, -1))
    rec = sphere.hit(ray, 0.001, float("inf"))
    assert rec is not None
    assert rec.front_face is False
    # ray started inside the sphere heading -z; the surface normal "seen"
    # by the ray points back the way it came, i.e. +z
    assert rec.normal == Vec3(0, 0, 1)


def test_sphere_respects_t_range():
    sphere = Sphere(Vec3(0, 0, -1), 0.5, make_material())
    ray = Ray(Vec3(0, 0, 0), Vec3(0, 0, -1))
    # both roots (0.5 and 1.5) are past t_max=0.4
    assert sphere.hit(ray, 0.001, 0.4) is None


def test_plane_hit():
    plane = Plane(Vec3(0, -1, 0), Vec3(0, 1, 0), make_material())
    ray = Ray(Vec3(0, 5, 0), Vec3(0, -1, 0))
    rec = plane.hit(ray, 0.001, float("inf"))
    assert rec is not None
    assert math.isclose(rec.t, 6.0)
    assert rec.point == Vec3(0, -1, 0)


def test_plane_parallel_ray_misses():
    plane = Plane(Vec3(0, -1, 0), Vec3(0, 1, 0), make_material())
    ray = Ray(Vec3(0, 5, 0), Vec3(1, 0, 0))
    assert plane.hit(ray, 0.001, float("inf")) is None


def test_hittable_list_returns_closest():
    near = Sphere(Vec3(0, 0, -1), 0.5, make_material())
    far = Sphere(Vec3(0, 0, -5), 0.5, make_material())
    world = HittableList([far, near])
    ray = Ray(Vec3(0, 0, 0), Vec3(0, 0, -1))
    rec = world.hit(ray, 0.001, float("inf"))
    assert rec is not None
    assert math.isclose(rec.t, 0.5)


def test_checker_plane_alternates_material():
    mat_a = make_material()
    mat_b = Lambertian(Vec3(0.1, 0.1, 0.1))
    plane = Plane(
        Vec3(0, 0, 0), Vec3(0, 1, 0), mat_a, checker_material=mat_b, checker_scale=1.0
    )
    assert plane._material_at(Vec3(0.5, 0, 0.5)) is mat_a
    assert plane._material_at(Vec3(1.5, 0, 0.5)) is mat_b


def test_sphere_bounding_box():
    sphere = Sphere(Vec3(1, 2, 3), 2.0, make_material())
    box = sphere.bounding_box()
    assert box is not None
    assert box.minimum == Vec3(-1, 0, 1)
    assert box.maximum == Vec3(3, 4, 5)


def test_plane_is_unbounded():
    plane = Plane(Vec3(0, 0, 0), Vec3(0, 1, 0), make_material())
    assert plane.bounding_box() is None
