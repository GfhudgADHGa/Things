"""A fully-connected (dense) layer: y = activation(x @ W + b)."""
from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple

from .activations import Activation


class Dense:
    def __init__(self, in_dim: int, out_dim: int, activation: Activation, rng: Optional[random.Random] = None):
        rng = rng or random.Random()
        self.in_dim = in_dim
        self.out_dim = out_dim
        self.activation = activation

        # a simple Xavier/Glorot-style init: keeps initial activations from
        # exploding or vanishing regardless of layer width
        scale = 1.0 / math.sqrt(in_dim)
        self.weights: List[List[float]] = [
            [rng.uniform(-scale, scale) for _ in range(out_dim)] for _ in range(in_dim)
        ]
        self.biases: List[float] = [0.0] * out_dim

        # momentum velocity, same shape as weights/biases, persists across
        # apply_gradients calls; stays all-zero (and thus a no-op) unless
        # a nonzero momentum coefficient is actually passed in.
        self._velocity_weights: List[List[float]] = [[0.0] * out_dim for _ in range(in_dim)]
        self._velocity_biases: List[float] = [0.0] * out_dim

        self._last_input: Optional[List[float]] = None
        self._last_output: Optional[List[float]] = None

    def forward(self, x: List[float]) -> List[float]:
        self._last_input = x
        z = [
            sum(x[i] * self.weights[i][j] for i in range(self.in_dim)) + self.biases[j]
            for j in range(self.out_dim)
        ]
        y = [self.activation.forward(zj) for zj in z]
        self._last_output = y
        return y

    def backward(self, grad_output: List[float]) -> Tuple[List[float], List[List[float]], List[float]]:
        """Given dL/dy, returns (dL/dx, dL/dW, dL/db). Pure computation --
        does not mutate the layer's weights (see apply_gradients for that),
        which is what makes numerical gradient checking possible: you need
        to be able to compute a gradient and then perturb a weight to check
        it, without the act of computing having already changed the weight.
        """
        grad_z = [
            grad_output[j] * self.activation.derivative_from_output(self._last_output[j])
            for j in range(self.out_dim)
        ]

        grad_weights = [
            [grad_z[j] * self._last_input[i] for j in range(self.out_dim)] for i in range(self.in_dim)
        ]
        grad_biases = list(grad_z)
        grad_input = [
            sum(grad_z[j] * self.weights[i][j] for j in range(self.out_dim)) for i in range(self.in_dim)
        ]

        return grad_input, grad_weights, grad_biases

    def apply_gradients(
        self,
        grad_weights: List[List[float]],
        grad_biases: List[float],
        learning_rate: float,
        momentum: float = 0.0,
    ) -> None:
        """Classic momentum SGD: v = momentum*v - lr*grad; w += v. With
        momentum=0.0 (the default) v is recomputed fresh from -lr*grad
        every call, which is exactly plain SGD -- so this is a strict
        superset of the old behavior, not a different code path."""
        for i in range(self.in_dim):
            row = self.weights[i]
            grad_row = grad_weights[i]
            v_row = self._velocity_weights[i]
            for j in range(self.out_dim):
                v_row[j] = momentum * v_row[j] - learning_rate * grad_row[j]
                row[j] += v_row[j]
        for j in range(self.out_dim):
            self._velocity_biases[j] = momentum * self._velocity_biases[j] - learning_rate * grad_biases[j]
            self.biases[j] += self._velocity_biases[j]
