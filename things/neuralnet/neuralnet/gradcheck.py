"""Numerical gradient checking: the standard way to verify a backprop
implementation, independent of trusting the calculus was transcribed
correctly into code. For each weight, nudge it by +/-epsilon, measure how
much the loss actually changes, and compare that finite-difference
estimate against what backward() claims the gradient is. If they don't
agree to several significant figures, the analytical gradient is wrong --
this catches sign errors, transposed indices, and missing terms that
would otherwise just look like "the network trains a bit worse than it
should," which is very easy to miss by eye.
"""
from __future__ import annotations

from typing import List

from .losses import Loss
from .network import Sequential


def max_relative_gradient_error(
    network: Sequential, x: List[float], y: List[float], loss_fn: Loss, epsilon: float = 1e-4
) -> float:
    pred = network.forward(x)
    grad = loss_fn.backward(pred, y)
    analytical: List[tuple] = []
    for layer in reversed(network.layers):
        grad, grad_weights, grad_biases = layer.backward(grad)
        analytical.append((layer, grad_weights, grad_biases))
    analytical.reverse()

    def loss_with_weight_perturbed(layer, i, j, delta) -> float:
        original = layer.weights[i][j]
        layer.weights[i][j] = original + delta
        result = loss_fn.forward(network.forward(x), y)
        layer.weights[i][j] = original
        return result

    max_error = 0.0

    for layer, grad_weights, grad_biases in analytical:
        for i in range(layer.in_dim):
            for j in range(layer.out_dim):
                plus = loss_with_weight_perturbed(layer, i, j, epsilon)
                minus = loss_with_weight_perturbed(layer, i, j, -epsilon)
                numerical = (plus - minus) / (2 * epsilon)
                analytical_value = grad_weights[i][j]
                max_error = max(max_error, _relative_error(numerical, analytical_value))

        for j in range(layer.out_dim):
            original = layer.biases[j]
            layer.biases[j] = original + epsilon
            plus = loss_fn.forward(network.forward(x), y)
            layer.biases[j] = original - epsilon
            minus = loss_fn.forward(network.forward(x), y)
            layer.biases[j] = original

            numerical = (plus - minus) / (2 * epsilon)
            max_error = max(max_error, _relative_error(numerical, grad_biases[j]))

    return max_error


def _relative_error(numerical: float, analytical: float) -> float:
    denom = max(abs(numerical), abs(analytical), 1e-8)
    return abs(numerical - analytical) / denom
