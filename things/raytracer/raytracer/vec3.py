"""A minimal 3D vector class, also used to represent RGB colors."""
from __future__ import annotations

import math
import random


class Vec3:
    __slots__ = ("x", "y", "z")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, o: "Vec3") -> "Vec3":
        return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)

    def __sub__(self, o: "Vec3") -> "Vec3":
        return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)

    def __neg__(self) -> "Vec3":
        return Vec3(-self.x, -self.y, -self.z)

    def __mul__(self, o) -> "Vec3":
        if isinstance(o, Vec3):
            return Vec3(self.x * o.x, self.y * o.y, self.z * o.z)
        return Vec3(self.x * o, self.y * o, self.z * o)

    __rmul__ = __mul__

    def __truediv__(self, t: float) -> "Vec3":
        inv = 1.0 / t
        return Vec3(self.x * inv, self.y * inv, self.z * inv)

    def __eq__(self, o) -> bool:
        return isinstance(o, Vec3) and self.x == o.x and self.y == o.y and self.z == o.z

    def __repr__(self) -> str:
        return f"Vec3({self.x!r}, {self.y!r}, {self.z!r})"

    def dot(self, o: "Vec3") -> float:
        return self.x * o.x + self.y * o.y + self.z * o.z

    def cross(self, o: "Vec3") -> "Vec3":
        return Vec3(
            self.y * o.z - self.z * o.y,
            self.z * o.x - self.x * o.z,
            self.x * o.y - self.y * o.x,
        )

    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y + self.z * self.z

    def length(self) -> float:
        return math.sqrt(self.length_squared())

    def normalized(self) -> "Vec3":
        return self / self.length()

    def near_zero(self, eps: float = 1e-8) -> bool:
        return abs(self.x) < eps and abs(self.y) < eps and abs(self.z) < eps

    def reflect(self, normal: "Vec3") -> "Vec3":
        return self - normal * (2 * self.dot(normal))

    def refract(self, normal: "Vec3", etai_over_etat: float) -> "Vec3":
        cos_theta = min((-self).dot(normal), 1.0)
        r_out_perp = (self + normal * cos_theta) * etai_over_etat
        r_out_parallel = normal * -math.sqrt(abs(1.0 - r_out_perp.length_squared()))
        return r_out_perp + r_out_parallel

    def as_tuple(self):
        return (self.x, self.y, self.z)

    @staticmethod
    def random(lo: float = 0.0, hi: float = 1.0) -> "Vec3":
        return Vec3(
            random.uniform(lo, hi), random.uniform(lo, hi), random.uniform(lo, hi)
        )

    @staticmethod
    def random_in_unit_sphere() -> "Vec3":
        while True:
            p = Vec3.random(-1, 1)
            if p.length_squared() < 1:
                return p

    @staticmethod
    def random_unit_vector() -> "Vec3":
        return Vec3.random_in_unit_sphere().normalized()

    @staticmethod
    def random_in_unit_disk() -> "Vec3":
        while True:
            p = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), 0)
            if p.length_squared() < 1:
                return p


def lerp(a: Vec3, b: Vec3, t: float) -> Vec3:
    return a * (1.0 - t) + b * t
