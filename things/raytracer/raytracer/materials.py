"""Surface materials: each knows how to scatter an incoming ray."""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Optional, Tuple

from .ray import Ray
from .vec3 import Vec3


class Material(ABC):
    @abstractmethod
    def scatter(self, ray_in: Ray, hit_record) -> Optional[Tuple[Vec3, Ray]]:
        """Return (attenuation, scattered_ray), or None if absorbed."""
        raise NotImplementedError


class Lambertian(Material):
    """Matte/diffuse surface."""

    def __init__(self, albedo: Vec3):
        self.albedo = albedo

    def scatter(self, ray_in: Ray, hit_record) -> Optional[Tuple[Vec3, Ray]]:
        scatter_direction = hit_record.normal + Vec3.random_unit_vector()
        if scatter_direction.near_zero():
            scatter_direction = hit_record.normal
        scattered = Ray(hit_record.point, scatter_direction)
        return self.albedo, scattered


class Metal(Material):
    """Reflective surface with optional fuzziness."""

    def __init__(self, albedo: Vec3, fuzz: float = 0.0):
        self.albedo = albedo
        self.fuzz = min(fuzz, 1.0)

    def scatter(self, ray_in: Ray, hit_record) -> Optional[Tuple[Vec3, Ray]]:
        reflected = ray_in.direction.normalized().reflect(hit_record.normal)
        scattered = Ray(
            hit_record.point, reflected + Vec3.random_in_unit_sphere() * self.fuzz
        )
        if scattered.direction.dot(hit_record.normal) <= 0:
            return None
        return self.albedo, scattered


class Dielectric(Material):
    """Clear refractive material (glass, water)."""

    def __init__(self, refraction_index: float):
        self.refraction_index = refraction_index

    @staticmethod
    def _reflectance(cosine: float, ref_idx: float) -> float:
        r0 = ((1 - ref_idx) / (1 + ref_idx)) ** 2
        return r0 + (1 - r0) * ((1 - cosine) ** 5)

    def scatter(self, ray_in: Ray, hit_record) -> Optional[Tuple[Vec3, Ray]]:
        attenuation = Vec3(1.0, 1.0, 1.0)
        refraction_ratio = (
            1.0 / self.refraction_index
            if hit_record.front_face
            else self.refraction_index
        )

        unit_direction = ray_in.direction.normalized()
        cos_theta = min((-unit_direction).dot(hit_record.normal), 1.0)
        sin_theta = (1.0 - cos_theta * cos_theta) ** 0.5

        cannot_refract = refraction_ratio * sin_theta > 1.0
        if cannot_refract or self._reflectance(
            cos_theta, refraction_ratio
        ) > random.random():
            direction = unit_direction.reflect(hit_record.normal)
        else:
            direction = unit_direction.refract(hit_record.normal, refraction_ratio)

        scattered = Ray(hit_record.point, direction)
        return attenuation, scattered
