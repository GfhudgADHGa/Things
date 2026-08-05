import math

from raytracer.camera import Camera
from raytracer.vec3 import Vec3


def test_camera_center_ray_points_at_look_at():
    look_from = Vec3(0, 0, 5)
    look_at = Vec3(0, 0, 0)
    cam = Camera(
        look_from, look_at, Vec3(0, 1, 0), vfov_degrees=90, aspect_ratio=1.0
    )
    ray = cam.get_ray(0.5, 0.5)
    direction = ray.direction.normalized()
    expected = (look_at - look_from).normalized()
    assert math.isclose(direction.x, expected.x, abs_tol=1e-9)
    assert math.isclose(direction.y, expected.y, abs_tol=1e-9)
    assert math.isclose(direction.z, expected.z, abs_tol=1e-9)


def test_camera_with_zero_aperture_has_fixed_origin():
    cam = Camera(
        Vec3(0, 0, 5), Vec3(0, 0, 0), Vec3(0, 1, 0), vfov_degrees=60, aspect_ratio=1.6
    )
    r1 = cam.get_ray(0.1, 0.9)
    r2 = cam.get_ray(0.9, 0.1)
    assert r1.origin == Vec3(0, 0, 5)
    assert r2.origin == Vec3(0, 0, 5)


def test_camera_corners_diverge_from_center():
    cam = Camera(
        Vec3(0, 0, 5), Vec3(0, 0, 0), Vec3(0, 1, 0), vfov_degrees=90, aspect_ratio=1.0
    )
    center = cam.get_ray(0.5, 0.5).direction.normalized()
    corner = cam.get_ray(0.0, 0.0).direction.normalized()
    assert not math.isclose(center.x, corner.x, abs_tol=1e-6)
