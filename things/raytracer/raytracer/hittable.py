"""Scene objects that a ray can intersect."""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from .ray import Ray
from .vec3 import Vec3


@dataclass
class HitRecord:
    point: Vec3
    normal: Vec3
    t: float
    front_face: bool
    material: object

    @staticmethod
    def face_normal(ray: Ray, outward_normal: Vec3):
        front_face = ray.direction.dot(outward_normal) < 0
        normal = outward_normal if front_face else -outward_normal
        return front_face, normal


class Hittable(ABC):
    @abstractmethod
    def hit(self, ray: Ray, t_min: float, t_max: float) -> Optional[HitRecord]:
        raise NotImplementedError


class Sphere(Hittable):
    def __init__(self, center: Vec3, radius: float, material):
        self.center = center
        self.radius = radius
        self.material = material

    def hit(self, ray: Ray, t_min: float, t_max: float) -> Optional[HitRecord]:
        oc = ray.origin - self.center
        a = ray.direction.length_squared()
        half_b = oc.dot(ray.direction)
        c = oc.length_squared() - self.radius * self.radius
        discriminant = half_b * half_b - a * c
        if discriminant < 0:
            return None
        sqrt_d = math.sqrt(discriminant)

        root = (-half_b - sqrt_d) / a
        if root < t_min or root > t_max:
            root = (-half_b + sqrt_d) / a
            if root < t_min or root > t_max:
                return None

        point = ray.at(root)
        outward_normal = (point - self.center) / self.radius
        front_face, normal = HitRecord.face_normal(ray, outward_normal)
        return HitRecord(point, normal, root, front_face, self.material)


class Plane(Hittable):
    """An infinite plane, optionally checkerboard-textured via two materials."""

    def __init__(
        self,
        point: Vec3,
        normal: Vec3,
        material,
        checker_material: Optional[object] = None,
        checker_scale: float = 1.0,
    ):
        self.point = point
        self.normal = normal.normalized()
        self.material = material
        self.checker_material = checker_material
        self.checker_scale = checker_scale

    def _material_at(self, point: Vec3):
        if self.checker_material is None:
            return self.material
        s = self.checker_scale
        cell = math.floor(point.x / s) + math.floor(point.z / s)
        return self.material if cell % 2 == 0 else self.checker_material

    def hit(self, ray: Ray, t_min: float, t_max: float) -> Optional[HitRecord]:
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 1e-8:
            return None
        t = (self.point - ray.origin).dot(self.normal) / denom
        if t < t_min or t > t_max:
            return None
        point = ray.at(t)
        front_face, normal = HitRecord.face_normal(ray, self.normal)
        return HitRecord(point, normal, t, front_face, self._material_at(point))


class HittableList(Hittable):
    def __init__(self, objects: Optional[List[Hittable]] = None):
        self.objects: List[Hittable] = objects or []

    def add(self, obj: Hittable) -> None:
        self.objects.append(obj)

    def hit(self, ray: Ray, t_min: float, t_max: float) -> Optional[HitRecord]:
        closest = t_max
        best: Optional[HitRecord] = None
        for obj in self.objects:
            rec = obj.hit(ray, t_min, closest)
            if rec is not None:
                closest = rec.t
                best = rec
        return best
