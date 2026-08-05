from __future__ import annotations

import math

from .ray import Ray
from .vec3 import Vec3


class Camera:
    def __init__(
        self,
        look_from: Vec3,
        look_at: Vec3,
        v_up: Vec3,
        vfov_degrees: float,
        aspect_ratio: float,
        aperture: float = 0.0,
        focus_dist: float | None = None,
    ):
        theta = math.radians(vfov_degrees)
        h = math.tan(theta / 2)
        viewport_height = 2.0 * h
        viewport_width = aspect_ratio * viewport_height

        self.w = (look_from - look_at).normalized()
        self.u = v_up.cross(self.w).normalized()
        self.v = self.w.cross(self.u)

        if focus_dist is None:
            focus_dist = (look_from - look_at).length()

        self.origin = look_from
        self.horizontal = self.u * viewport_width * focus_dist
        self.vertical = self.v * viewport_height * focus_dist
        self.lower_left_corner = (
            self.origin
            - self.horizontal / 2
            - self.vertical / 2
            - self.w * focus_dist
        )
        self.lens_radius = aperture / 2

    def get_ray(self, s: float, t: float) -> Ray:
        rd = Vec3.random_in_unit_disk() * self.lens_radius
        offset = self.u * rd.x + self.v * rd.y
        origin = self.origin + offset
        direction = (
            self.lower_left_corner + self.horizontal * s + self.vertical * t
            - self.origin
            - offset
        )
        return Ray(origin, direction)
