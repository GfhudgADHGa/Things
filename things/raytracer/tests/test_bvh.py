import random

import pytest

from raytracer.bvh import BVHNode
from raytracer.hittable import HittableList, Sphere
from raytracer.materials import Lambertian
from raytracer.ray import Ray
from raytracer.vec3 import Vec3


def random_spheres(n, seed):
    rng = random.Random(seed)
    material = Lambertian(Vec3(0.5, 0.5, 0.5))
    return [
        Sphere(
            Vec3(rng.uniform(-10, 10), rng.uniform(-10, 10), rng.uniform(-10, 10)),
            rng.uniform(0.2, 1.5),
            material,
        )
        for _ in range(n)
    ]


def test_bvh_requires_at_least_one_object():
    with pytest.raises(ValueError):
        BVHNode([])


def test_bvh_bounding_box_encloses_all_children():
    spheres = random_spheres(20, seed=1)
    bvh = BVHNode(spheres, rng=random.Random(0))
    box = bvh.bounding_box()
    for sphere in spheres:
        sbox = sphere.bounding_box()
        assert box.minimum.x <= sbox.minimum.x
        assert box.minimum.y <= sbox.minimum.y
        assert box.minimum.z <= sbox.minimum.z
        assert box.maximum.x >= sbox.maximum.x
        assert box.maximum.y >= sbox.maximum.y
        assert box.maximum.z >= sbox.maximum.z


def test_bvh_matches_brute_force_hittable_list_on_random_rays():
    spheres = random_spheres(60, seed=2)
    bvh = BVHNode(spheres, rng=random.Random(0))
    brute_force = HittableList(spheres)

    rng = random.Random(3)
    for _ in range(300):
        origin = Vec3(rng.uniform(-15, 15), rng.uniform(-15, 15), rng.uniform(-15, 15))
        direction = Vec3(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))
        if direction.length_squared() < 1e-9:
            continue
        ray = Ray(origin, direction.normalized())

        bvh_hit = bvh.hit(ray, 0.001, float("inf"))
        brute_hit = brute_force.hit(ray, 0.001, float("inf"))

        assert (bvh_hit is None) == (brute_hit is None)
        if bvh_hit is not None:
            assert bvh_hit.t == pytest.approx(brute_hit.t, abs=1e-9)
            assert bvh_hit.point.x == pytest.approx(brute_hit.point.x, abs=1e-9)
            assert bvh_hit.point.y == pytest.approx(brute_hit.point.y, abs=1e-9)
            assert bvh_hit.point.z == pytest.approx(brute_hit.point.z, abs=1e-9)


def test_bvh_single_object():
    sphere = Sphere(Vec3(0, 0, -5), 1.0, Lambertian(Vec3(1, 1, 1)))
    bvh = BVHNode([sphere])
    ray = Ray(Vec3(0, 0, 0), Vec3(0, 0, -1))
    rec = bvh.hit(ray, 0.001, float("inf"))
    assert rec is not None
    assert rec.t == pytest.approx(4.0)


def test_bvh_two_objects_returns_closer_one():
    near = Sphere(Vec3(0, 0, -3), 0.5, Lambertian(Vec3(1, 0, 0)))
    far = Sphere(Vec3(0, 0, -8), 0.5, Lambertian(Vec3(0, 0, 1)))
    bvh = BVHNode([far, near])
    ray = Ray(Vec3(0, 0, 0), Vec3(0, 0, -1))
    rec = bvh.hit(ray, 0.001, float("inf"))
    assert rec.material is near.material


def test_bvh_ray_missing_everything_returns_none():
    spheres = random_spheres(30, seed=5)
    bvh = BVHNode(spheres, rng=random.Random(1))
    ray = Ray(Vec3(1000, 1000, 1000), Vec3(1, 0, 0))
    assert bvh.hit(ray, 0.001, float("inf")) is None


def test_bvh_rejects_objects_without_bounding_box():
    from raytracer.hittable import Plane

    plane = Plane(Vec3(0, 0, 0), Vec3(0, 1, 0), Lambertian(Vec3(1, 1, 1)))
    with pytest.raises(ValueError):
        BVHNode([plane])
