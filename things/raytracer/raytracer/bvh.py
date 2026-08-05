"""Bounding Volume Hierarchy: a binary tree over bounded objects that lets
the ray tracer skip whole subtrees whose bounding box the ray never enters,
instead of testing every object against every ray.
"""
from __future__ import annotations

import random
from typing import List, Optional

from .aabb import AABB
from .hittable import HitRecord, Hittable
from .ray import Ray


class BVHNode(Hittable):
    def __init__(self, objects: List[Hittable], rng: Optional[random.Random] = None):
        rng = rng or random
        objects = list(objects)
        if not objects:
            raise ValueError("BVHNode requires at least one object")

        boxes = [obj.bounding_box() for obj in objects]
        if any(b is None for b in boxes):
            raise ValueError("BVHNode requires every object to have a bounding_box()")

        axis = rng.choice(("x", "y", "z"))
        objects_and_boxes = sorted(
            zip(objects, boxes), key=lambda ob: getattr(ob[1].minimum, axis)
        )
        objects = [ob[0] for ob in objects_and_boxes]

        if len(objects) == 1:
            self.left: Hittable = objects[0]
            self.right: Hittable = objects[0]
        elif len(objects) == 2:
            self.left, self.right = objects[0], objects[1]
        else:
            mid = len(objects) // 2
            self.left = BVHNode(objects[:mid], rng)
            self.right = BVHNode(objects[mid:], rng)

        self.box = AABB.surrounding(self.left.bounding_box(), self.right.bounding_box())

    def bounding_box(self) -> Optional[AABB]:
        return self.box

    def hit(self, ray: Ray, t_min: float, t_max: float) -> Optional[HitRecord]:
        if not self.box.hit(ray, t_min, t_max):
            return None

        hit_left = self.left.hit(ray, t_min, t_max)
        right_t_max = hit_left.t if hit_left is not None else t_max
        hit_right = self.right.hit(ray, t_min, right_t_max)

        return hit_right if hit_right is not None else hit_left
