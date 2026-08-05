"""Turns a scene (camera + world) into a grid of pixels."""
from __future__ import annotations

import multiprocessing as mp
import random
from typing import List, Tuple

from .ray import Ray
from .vec3 import Vec3, lerp

Color = Tuple[int, int, int]

_SKY_TOP = Vec3(0.5, 0.7, 1.0)
_SKY_BOTTOM = Vec3(1.0, 1.0, 1.0)


def ray_color(ray: Ray, world, depth: int) -> Vec3:
    if depth <= 0:
        return Vec3(0, 0, 0)

    rec = world.hit(ray, 0.001, float("inf"))
    if rec is not None:
        scatter = rec.material.scatter(ray, rec)
        if scatter is None:
            return Vec3(0, 0, 0)
        attenuation, scattered = scatter
        return attenuation * ray_color(scattered, world, depth - 1)

    unit_direction = ray.direction.normalized()
    t = 0.5 * (unit_direction.y + 1.0)
    return lerp(_SKY_BOTTOM, _SKY_TOP, t)


def _to_byte_color(c: Vec3, samples_per_pixel: int) -> Color:
    scale = 1.0 / samples_per_pixel
    r = (c.x * scale) ** 0.5
    g = (c.y * scale) ** 0.5
    b = (c.z * scale) ** 0.5
    clamp = lambda v: max(0, min(255, int(256 * max(0.0, min(0.999, v)))))
    return clamp(r), clamp(g), clamp(b)


def _render_row(args) -> Tuple[int, List[Color]]:
    row_index, image_width, image_height, samples_per_pixel, max_depth, camera, world, seed = args
    random.seed(seed + row_index)
    row: List[Color] = []
    j = image_height - 1 - row_index
    for i in range(image_width):
        color = Vec3(0, 0, 0)
        for _ in range(samples_per_pixel):
            u = (i + random.random()) / (image_width - 1)
            v = (j + random.random()) / (image_height - 1)
            r = camera.get_ray(u, v)
            color = color + ray_color(r, world, max_depth)
        row.append(_to_byte_color(color, samples_per_pixel))
    return row_index, row


def render(
    world,
    camera,
    image_width: int = 400,
    image_height: int = 225,
    samples_per_pixel: int = 50,
    max_depth: int = 10,
    seed: int = 0,
    workers: int | None = None,
) -> List[List[Color]]:
    """Renders the scene and returns a list of rows (top to bottom) of (r, g, b) tuples."""
    tasks = [
        (row, image_width, image_height, samples_per_pixel, max_depth, camera, world, seed)
        for row in range(image_height)
    ]

    results: dict[int, List[Color]] = {}
    if workers == 1:
        for task in tasks:
            row_index, row = _render_row(task)
            results[row_index] = row
    else:
        with mp.Pool(processes=workers) as pool:
            for row_index, row in pool.imap_unordered(_render_row, tasks):
                results[row_index] = row

    return [results[i] for i in range(image_height)]
