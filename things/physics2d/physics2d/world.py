"""A small 2D rigid-body simulation: gravity, walls, and elastic
circle-circle collisions resolved with impulses (the standard technique --
apply an instantaneous velocity change along the collision normal so the
pair separates, sized by their combined restitution and masses).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .body import Circle
from .vec2 import Vec2

POSITIONAL_CORRECTION_PERCENT = 0.8
POSITIONAL_CORRECTION_SLOP = 0.01


@dataclass
class World:
    width: float
    height: float
    gravity: Vec2 = field(default_factory=lambda: Vec2(0, 800))
    bodies: List[Circle] = field(default_factory=list)

    def add(self, body: Circle) -> None:
        self.bodies.append(body)

    def step(self, dt: float) -> None:
        for body in self.bodies:
            if body.static:
                continue
            body.velocity = body.velocity + self.gravity * dt
            body.position = body.position + body.velocity * dt

        for body in self.bodies:
            self._resolve_walls(body)

        n = len(self.bodies)
        for i in range(n):
            for j in range(i + 1, n):
                self._resolve_pair(self.bodies[i], self.bodies[j])

    def _resolve_walls(self, body: Circle) -> None:
        if body.static:
            return
        r = body.radius

        if body.position.x - r < 0:
            body.position.x = r
            body.velocity.x = -body.velocity.x * body.restitution
        elif body.position.x + r > self.width:
            body.position.x = self.width - r
            body.velocity.x = -body.velocity.x * body.restitution

        if body.position.y - r < 0:
            body.position.y = r
            body.velocity.y = -body.velocity.y * body.restitution
        elif body.position.y + r > self.height:
            body.position.y = self.height - r
            body.velocity.y = -body.velocity.y * body.restitution

    def _resolve_pair(self, a: Circle, b: Circle) -> None:
        delta = b.position - a.position
        distance = delta.length()
        min_distance = a.radius + b.radius
        if distance >= min_distance or distance == 0:
            return

        normal = delta.normalized()
        inv_mass_sum = a.inverse_mass + b.inverse_mass
        if inv_mass_sum == 0:
            return  # both static/infinite mass: nothing to do

        relative_velocity = b.velocity - a.velocity
        vel_along_normal = relative_velocity.dot(normal)
        if vel_along_normal <= 0:
            restitution = min(a.restitution, b.restitution)
            j = -(1 + restitution) * vel_along_normal / inv_mass_sum
            impulse = normal * j
            a.velocity = a.velocity - impulse * a.inverse_mass
            b.velocity = b.velocity + impulse * b.inverse_mass

        overlap = min_distance - distance
        correction_mag = max(overlap - POSITIONAL_CORRECTION_SLOP, 0) / inv_mass_sum * POSITIONAL_CORRECTION_PERCENT
        correction = normal * correction_mag
        a.position = a.position - correction * a.inverse_mass
        b.position = b.position + correction * b.inverse_mass
