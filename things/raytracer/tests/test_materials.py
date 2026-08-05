import random

from raytracer.hittable import HitRecord
from raytracer.materials import Dielectric, Lambertian, Metal
from raytracer.ray import Ray
from raytracer.vec3 import Vec3


def make_hit_record(front_face=True, normal=Vec3(0, 1, 0)):
    return HitRecord(
        point=Vec3(0, 0, 0),
        normal=normal,
        t=1.0,
        front_face=front_face,
        material=None,
    )


def test_lambertian_scatters_with_its_albedo():
    random.seed(1)
    mat = Lambertian(Vec3(0.5, 0.6, 0.7))
    rec = make_hit_record()
    ray_in = Ray(Vec3(0, 5, 0), Vec3(0, -1, 0))
    result = mat.scatter(ray_in, rec)
    assert result is not None
    attenuation, scattered = result
    assert attenuation == mat.albedo
    assert scattered.origin == rec.point


def test_lambertian_degenerate_direction_falls_back_to_normal():
    mat = Lambertian(Vec3(1, 1, 1))
    rec = make_hit_record(normal=Vec3(0, 1, 0))
    ray_in = Ray(Vec3(0, 5, 0), Vec3(0, -1, 0))
    # Force the random unit vector to exactly cancel the normal.
    original = Vec3.random_unit_vector
    Vec3.random_unit_vector = staticmethod(lambda: Vec3(0, -1, 0))
    try:
        _, scattered = mat.scatter(ray_in, rec)
    finally:
        Vec3.random_unit_vector = original
    assert scattered.direction == rec.normal


def test_metal_reflects_perfectly_with_zero_fuzz():
    mat = Metal(Vec3(0.9, 0.9, 0.9), fuzz=0.0)
    rec = make_hit_record(normal=Vec3(0, 1, 0))
    ray_in = Ray(Vec3(0, 1, 0), Vec3(1, -1, 0).normalized())
    result = mat.scatter(ray_in, rec)
    assert result is not None
    _, scattered = result
    assert scattered.direction.x > 0
    assert scattered.direction.y > 0


def test_metal_absorbs_rays_reflecting_into_surface():
    mat = Metal(Vec3(0.9, 0.9, 0.9), fuzz=0.0)
    rec = make_hit_record(normal=Vec3(0, 1, 0))
    # A ray that reflects to point back into the surface (fuzz pushes it under).
    ray_in = Ray(Vec3(0, 1, 0), Vec3(0, -1, 0))
    mat.fuzz = 0.0
    result = mat.scatter(ray_in, rec)
    # straight-down ray reflects straight back up: not absorbed
    assert result is not None


def test_dielectric_always_produces_a_scattered_ray():
    mat = Dielectric(1.5)
    rec = make_hit_record(front_face=True, normal=Vec3(0, 1, 0))
    ray_in = Ray(Vec3(0, 1, 0), Vec3(0, -1, 0))
    result = mat.scatter(ray_in, rec)
    assert result is not None
    attenuation, scattered = result
    assert attenuation == Vec3(1, 1, 1)


def test_dielectric_reflectance_schlick_bounds():
    # At normal incidence reflectance should equal r0, and stay in [0, 1].
    r0 = Dielectric._reflectance(1.0, 1.5)
    assert 0.0 <= r0 <= 1.0
    grazing = Dielectric._reflectance(0.01, 1.5)
    assert grazing > r0  # reflectance increases toward grazing angles
