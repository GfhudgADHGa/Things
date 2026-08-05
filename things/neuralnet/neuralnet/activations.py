"""Activation functions, each paired with its derivative expressed in
terms of the function's own *output* (the standard backprop convenience
form -- e.g. sigmoid'(x) = sigmoid(x) * (1 - sigmoid(x)), so the backward
pass can reuse the value already computed on the forward pass instead of
recomputing sigmoid(x) from scratch).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable


@dataclass
class Activation:
    name: str
    forward: Callable[[float], float]
    derivative_from_output: Callable[[float], float]


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


SIGMOID = Activation(
    name="sigmoid",
    forward=_sigmoid,
    derivative_from_output=lambda y: y * (1.0 - y),
)

RELU = Activation(
    name="relu",
    forward=lambda x: x if x > 0 else 0.0,
    derivative_from_output=lambda y: 1.0 if y > 0 else 0.0,
)

TANH = Activation(
    name="tanh",
    forward=math.tanh,
    derivative_from_output=lambda y: 1.0 - y * y,
)

LINEAR = Activation(
    name="linear",
    forward=lambda x: x,
    derivative_from_output=lambda y: 1.0,
)

BY_NAME = {a.name: a for a in (SIGMOID, RELU, TANH, LINEAR)}
