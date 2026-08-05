"""Loss functions, each with a forward (scalar loss) and backward
(dL/dprediction, one gradient per output unit) form.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, List

_EPS = 1e-12


@dataclass
class Loss:
    name: str
    forward: Callable[[List[float], List[float]], float]
    backward: Callable[[List[float], List[float]], List[float]]


def _mse_forward(pred: List[float], target: List[float]) -> float:
    return sum((p - t) ** 2 for p, t in zip(pred, target)) / len(pred)


def _mse_backward(pred: List[float], target: List[float]) -> List[float]:
    n = len(pred)
    return [2.0 * (p - t) / n for p, t in zip(pred, target)]


MSE = Loss(name="mse", forward=_mse_forward, backward=_mse_backward)


def _clip(p: float) -> float:
    return min(max(p, _EPS), 1.0 - _EPS)


def _bce_forward(pred: List[float], target: List[float]) -> float:
    n = len(pred)
    total = 0.0
    for p, t in zip(pred, target):
        p = _clip(p)
        total += -(t * math.log(p) + (1 - t) * math.log(1 - p))
    return total / n


def _bce_backward(pred: List[float], target: List[float]) -> List[float]:
    n = len(pred)
    grads = []
    for p, t in zip(pred, target):
        p = _clip(p)
        grads.append((-(t / p) + (1 - t) / (1 - p)) / n)
    return grads


BINARY_CROSS_ENTROPY = Loss(name="binary_cross_entropy", forward=_bce_forward, backward=_bce_backward)
