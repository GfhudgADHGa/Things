"""A handful of example scenes."""
from __future__ import annotations

import random

from .bvh import BVHNode
from .camera import Camera
from .hittable import HittableList, Plane, Sphere
from .materials import Dielectric, Lambertian, Metal
from .vec3 import Vec3


def three_spheres(aspect_ratio: float = 16 / 9):
    """Three spheres of the three material types, sitting on a checkered floor."""
    world = HittableList()

    floor = Lambertian(Vec3(0.9, 0.9, 0.9))
    floor_dark = Lambertian(Vec3(0.2, 0.2, 0.25))
    world.add(
        Plane(
            Vec3(0, -0.5, 0),
            Vec3(0, 1, 0),
            floor,
            checker_material=floor_dark,
            checker_scale=1.0,
        )
    )

    world.add(Sphere(Vec3(0, 0, -1), 0.5, Lambertian(Vec3(0.75, 0.25, 0.25))))
    world.add(Sphere(Vec3(-1.1, 0, -1), 0.5, Dielectric(1.5)))
    world.add(Sphere(Vec3(-1.1, 0, -1), -0.45, Dielectric(1.5)))
    world.add(Sphere(Vec3(1.1, 0, -1), 0.5, Metal(Vec3(0.8, 0.8, 0.85), 0.05)))

    look_from = Vec3(0, 1.2, 2.8)
    look_at = Vec3(0, 0, -1)
    camera = Camera(
        look_from,
        look_at,
        Vec3(0, 1, 0),
        vfov_degrees=40,
        aspect_ratio=aspect_ratio,
        aperture=0.05,
        focus_dist=(look_from - look_at).length(),
    )
    return world, camera


def random_field(aspect_ratio: float = 3 / 2, seed: int = 42, n: int = 5):
    """A field of small random spheres around three large feature spheres.

    Loosely inspired by the cover render of "Ray Tracing in One Weekend".
    """
    rng = random.Random(seed)
    world = HittableList()
    spheres = []

    floor = Lambertian(Vec3(0.5, 0.5, 0.5))
    world.add(Plane(Vec3(0, 0, 0), Vec3(0, 1, 0), floor))

    for a in range(-n, n):
        for b in range(-n, n):
            center = Vec3(a + 0.9 * rng.random(), 0.2, b + 0.9 * rng.random())
            if (center - Vec3(4, 0.2, 0)).length() <= 0.9:
                continue
            if (center - Vec3(-4, 0.2, 0)).length() <= 0.9:
                continue
            if (center - Vec3(0, 0.2, 0)).length() <= 0.9:
                continue

            choice = rng.random()
            if choice < 0.8:
                albedo = Vec3(
                    rng.random() * rng.random(),
                    rng.random() * rng.random(),
                    rng.random() * rng.random(),
                )
                material = Lambertian(albedo)
            elif choice < 0.95:
                albedo = Vec3(
                    0.5 * (1 + rng.random()),
                    0.5 * (1 + rng.random()),
                    0.5 * (1 + rng.random()),
                )
                fuzz = 0.5 * rng.random()
                material = Metal(albedo, fuzz)
            else:
                material = Dielectric(1.5)

            spheres.append(Sphere(center, 0.2, material))

    spheres.append(Sphere(Vec3(0, 1, 0), 1.0, Dielectric(1.5)))
    spheres.append(Sphere(Vec3(-4, 1, 0), 1.0, Lambertian(Vec3(0.4, 0.2, 0.1))))
    spheres.append(Sphere(Vec3(4, 1, 0), 1.0, Metal(Vec3(0.7, 0.6, 0.5), 0.0)))

    # spheres go behind a BVH; the ground plane stays outside it (unbounded,
    # so it can't be part of the tree) and is tested directly every ray
    world.add(BVHNode(spheres, rng))

    look_from = Vec3(13, 2, 3)
    look_at = Vec3(0, 0, 0)
    camera = Camera(
        look_from,
        look_at,
        Vec3(0, 1, 0),
        vfov_degrees=20,
        aspect_ratio=aspect_ratio,
        aperture=0.1,
        focus_dist=10.0,
    )
    return world, camera


SCENES = {
    "three_spheres": three_spheres,
    "random_field": random_field,
}
