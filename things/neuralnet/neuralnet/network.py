"""A Sequential network: a stack of Dense layers trained by plain SGD."""
from __future__ import annotations

from typing import List

from .layer import Dense
from .losses import Loss


class Sequential:
    def __init__(self, layers: List[Dense]):
        self.layers = layers

    def forward(self, x: List[float]) -> List[float]:
        for layer in self.layers:
            x = layer.forward(x)
        return x

    def train_step(
        self, x: List[float], y: List[float], loss_fn: Loss, learning_rate: float, momentum: float = 0.0
    ) -> float:
        pred = self.forward(x)
        loss = loss_fn.forward(pred, y)

        grad = loss_fn.backward(pred, y)
        per_layer_grads = []
        for layer in reversed(self.layers):
            grad, grad_weights, grad_biases = layer.backward(grad)
            per_layer_grads.append((layer, grad_weights, grad_biases))

        for layer, grad_weights, grad_biases in per_layer_grads:
            layer.apply_gradients(grad_weights, grad_biases, learning_rate, momentum)

        return loss

    def train_epoch(
        self, dataset: List[tuple], loss_fn: Loss, learning_rate: float, momentum: float = 0.0
    ) -> float:
        total = 0.0
        for x, y in dataset:
            total += self.train_step(x, y, loss_fn, learning_rate, momentum)
        return total / len(dataset)
