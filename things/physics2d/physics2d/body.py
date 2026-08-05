from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .vec2 import Vec2


@dataclass
class Circle:
    position: Vec2
    velocity: Vec2
    radius: float
    mass: float = 1.0
    restitution: float = 0.8
    color: Tuple[int, int, int] = (220, 60, 60)
    static: bool = False

    @property
    def inverse_mass(self) -> float:
        return 0.0 if self.static else 1.0 / self.mass
