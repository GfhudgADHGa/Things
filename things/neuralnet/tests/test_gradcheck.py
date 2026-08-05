"""These are the tests that actually validate backprop is implemented
correctly -- not by re-deriving the calculus and checking it matches (that
would just duplicate the same potential mistake), but by comparing the
analytical gradient against an independent numerical estimate for every
single weight and bias in the network. See gradcheck.py's docstring.
"""
import random

import pytest

from neuralnet.activations import LINEAR, RELU, SIGMOID, TANH
from neuralnet.gradcheck import max_relative_gradient_error
from neuralnet.layer import Dense
from neuralnet.losses import BINARY_CROSS_ENTROPY, MSE
from neuralnet.network import Sequential

# A well-implemented backprop, checked with float64 and epsilon=1e-4,
# should agree with the numerical estimate to several significant figures.
# 1e-4 is a generous but meaningful bound -- large enough to not be flaky
# from floating-point noise, small enough that a real bug (a transposed
# index, a missing chain-rule term, a sign error) would blow right past it.
TOLERANCE = 1e-4


def test_single_linear_layer_mse():
    rng = random.Random(0)
    net = Sequential([Dense(3, 2, LINEAR, rng)])
    error = max_relative_gradient_error(net, [0.5, -0.3, 0.8], [1.0, -1.0], MSE)
    assert error < TOLERANCE


def test_single_sigmoid_layer_mse():
    rng = random.Random(1)
    net = Sequential([Dense(4, 3, SIGMOID, rng)])
    error = max_relative_gradient_error(net, [0.1, 0.2, -0.3, 0.4], [1.0, 0.0, 0.5], MSE)
    assert error < TOLERANCE


def test_single_relu_layer_mse():
    rng = random.Random(2)
    net = Sequential([Dense(3, 3, RELU, rng)])
    # deliberately mixed-sign input so some ReLU units are active and some aren't
    error = max_relative_gradient_error(net, [0.5, -0.5, 0.2], [0.3, 0.1, -0.2], MSE)
    assert error < TOLERANCE


def test_deep_network_mixed_activations_mse():
    rng = random.Random(3)
    net = Sequential([
        Dense(3, 6, TANH, rng),
        Dense(6, 5, RELU, rng),
        Dense(5, 4, SIGMOID, rng),
        Dense(4, 2, LINEAR, rng),
    ])
    error = max_relative_gradient_error(net, [0.5, -0.3, 0.8], [1.0, -1.0], MSE)
    assert error < TOLERANCE


def test_deep_network_binary_cross_entropy():
    rng = random.Random(4)
    net = Sequential([
        Dense(2, 5, TANH, rng),
        Dense(5, 3, TANH, rng),
        Dense(3, 1, SIGMOID, rng),
    ])
    error = max_relative_gradient_error(net, [0.3, 0.7], [1.0], BINARY_CROSS_ENTROPY)
    assert error < TOLERANCE


@pytest.mark.parametrize("seed", range(10))
def test_gradient_check_passes_across_many_random_networks(seed):
    rng = random.Random(seed)
    hidden = rng.randint(2, 8)
    net = Sequential([
        Dense(4, hidden, rng.choice([TANH, RELU, SIGMOID]), rng),
        Dense(hidden, 3, SIGMOID, rng),
    ])
    x = [rng.uniform(-1, 1) for _ in range(4)]
    y = [rng.uniform(0, 1) for _ in range(3)]
    error = max_relative_gradient_error(net, x, y, MSE)
    assert error < TOLERANCE, f"seed {seed}: error {error}"


def test_gradient_check_would_catch_a_deliberately_broken_gradient():
    """Sanity check on the checker itself: if we hand it a wrong gradient,
    does it actually notice? Without this, a gradcheck that always reports
    success would pass every test above for the wrong reason.
    """
    rng = random.Random(5)
    net = Sequential([Dense(2, 2, LINEAR, rng)])
    x, y = [1.0, 1.0], [0.0, 0.0]

    # monkeypatch backward() to return a deliberately wrong weight gradient
    layer = net.layers[0]
    original_backward = layer.backward

    def broken_backward(grad_output):
        grad_input, grad_weights, grad_biases = original_backward(grad_output)
        broken_weights = [[w + 10.0 for w in row] for row in grad_weights]
        return grad_input, broken_weights, grad_biases

    layer.backward = broken_backward
    error = max_relative_gradient_error(net, x, y, MSE)
    assert error > 0.5  # nowhere close to the numerical estimate
