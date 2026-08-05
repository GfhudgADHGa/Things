import os

from raytracer.png_writer import write_png
from raytracer.render import ray_color, render
from raytracer.ray import Ray
from raytracer.scenes import three_spheres
from raytracer.vec3 import Vec3


def test_ray_color_sky_gradient_when_nothing_hit():
    from raytracer.hittable import HittableList

    empty_world = HittableList()
    straight_up = Ray(Vec3(0, 0, 0), Vec3(0, 1, 0))
    color = ray_color(straight_up, empty_world, depth=5)
    # looking straight up should be the "top of sky" color
    assert color == Vec3(0.5, 0.7, 1.0)


def test_ray_color_returns_black_past_max_depth():
    from raytracer.hittable import HittableList

    empty_world = HittableList()
    ray = Ray(Vec3(0, 0, 0), Vec3(0, 1, 0))
    assert ray_color(ray, empty_world, depth=0) == Vec3(0, 0, 0)


def test_render_produces_correct_dimensions():
    world, camera = three_spheres()
    rows = render(
        world,
        camera,
        image_width=16,
        image_height=9,
        samples_per_pixel=2,
        max_depth=3,
        seed=7,
        workers=1,
    )
    assert len(rows) == 9
    assert all(len(row) == 16 for row in rows)
    for row in rows:
        for pixel in row:
            assert len(pixel) == 3
            assert all(0 <= channel <= 255 for channel in pixel)


def test_render_top_row_is_sky_colored():
    world, camera = three_spheres()
    rows = render(
        world,
        camera,
        image_width=8,
        image_height=8,
        samples_per_pixel=1,
        max_depth=2,
        seed=1,
        workers=1,
    )
    top_left = rows[0][0]
    # sky should read as light-ish, not the near-black of an unhit background bug
    assert sum(top_left) > 100


def test_render_is_deterministic_given_seed():
    world1, camera1 = three_spheres()
    world2, camera2 = three_spheres()
    rows1 = render(
        world1, camera1, image_width=10, image_height=6, samples_per_pixel=3,
        max_depth=3, seed=99, workers=1,
    )
    rows2 = render(
        world2, camera2, image_width=10, image_height=6, samples_per_pixel=3,
        max_depth=3, seed=99, workers=1,
    )
    assert rows1 == rows2


def test_write_png_stdlib_fallback_roundtrip(tmp_path):
    from raytracer import png_writer

    rows = [[(255, 0, 0), (0, 255, 0)], [(0, 0, 255), (255, 255, 255)]]
    out_path = tmp_path / "tiny.png"
    png_writer._write_png_stdlib(rows, str(out_path))

    assert out_path.exists()
    with open(out_path, "rb") as f:
        header = f.read(8)
    assert header == b"\x89PNG\r\n\x1a\n"


def test_write_png_via_pillow(tmp_path):
    rows = [[(10, 20, 30), (40, 50, 60)]]
    out_path = tmp_path / "tiny.png"
    write_png(rows, str(out_path))
    assert out_path.exists()
    assert os.path.getsize(str(out_path)) > 0
