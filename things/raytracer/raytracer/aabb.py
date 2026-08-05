"""Axis-aligned bounding boxes, used by the BVH to skip whole subtrees."""
from __future__ import annotations

from .ray import Ray
from .vec3 import Vec3


class AABB:
    __slots__ = ("minimum", "maximum")

    def __init__(self, minimum: Vec3, maximum: Vec3):
        self.minimum = minimum
        self.maximum = maximum

    def hit(self, ray: Ray, t_min: float, t_max: float) -> bool:
        for axis in ("x", "y", "z"):
            origin = getattr(ray.origin, axis)
            direction = getattr(ray.direction, axis)
            lo = getattr(self.minimum, axis)
            hi = getattr(self.maximum, axis)

            if direction == 0:
                if origin < lo or origin > hi:
                    return False
                continue

            inv_d = 1.0 / direction
            t0 = (lo - origin) * inv_d
            t1 = (hi - origin) * inv_d
            if inv_d < 0:
                t0, t1 = t1, t0

            t_min = max(t_min, t0)
            t_max = min(t_max, t1)
            if t_max <= t_min:
                return False

        return True

    @staticmethod
    def surrounding(a: "AABB", b: "AABB") -> "AABB":
        small = Vec3(
            min(a.minimum.x, b.minimum.x),
            min(a.minimum.y, b.minimum.y),
            min(a.minimum.z, b.minimum.z),
        )
        big = Vec3(
            max(a.maximum.x, b.maximum.x),
            max(a.maximum.y, b.maximum.y),
            max(a.maximum.z, b.maximum.z),
        )
        return AABB(small, big)
