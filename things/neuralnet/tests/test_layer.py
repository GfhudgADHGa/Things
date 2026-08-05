import random

from neuralnet.activations import LINEAR, RELU
from neuralnet.layer import Dense


def test_forward_output_shape():
    layer = Dense(3, 5, LINEAR, random.Random(0))
    y = layer.forward([1.0, 2.0, 3.0])
    assert len(y) == 5


def test_forward_linear_matches_manual_matmul():
    layer = Dense(2, 2, LINEAR, random.Random(0))
    layer.weights = [[1.0, 2.0], [3.0, 4.0]]
    layer.biases = [0.5, -0.5]
    x = [1.0, 1.0]
    y = layer.forward(x)
    # y[j] = sum_i x[i]*W[i][j] + b[j]
    assert y[0] == 1 * 1.0 + 1 * 3.0 + 0.5
    assert y[1] == 1 * 2.0 + 1 * 4.0 - 0.5


def test_relu_zeroes_negative_preactivations():
    layer = Dense(1, 1, RELU, random.Random(0))
    layer.weights = [[-1.0]]
    layer.biases = [0.0]
    y = layer.forward([5.0])
    assert y[0] == 0.0


def test_backward_returns_correct_shapes():
    layer = Dense(3, 2, LINEAR, random.Random(0))
    layer.forward([1.0, 2.0, 3.0])
    grad_input, grad_weights, grad_biases = layer.backward([1.0, 1.0])
    assert len(grad_input) == 3
    assert len(grad_weights) == 3
    assert all(len(row) == 2 for row in grad_weights)
    assert len(grad_biases) == 2


def test_backward_does_not_mutate_weights():
    layer = Dense(2, 2, LINEAR, random.Random(0))
    layer.forward([1.0, 1.0])
    weights_before = [row[:] for row in layer.weights]
    biases_before = layer.biases[:]
    layer.backward([1.0, 1.0])
    assert layer.weights == weights_before
    assert layer.biases == biases_before


def test_apply_gradients_moves_weights_in_descent_direction():
    layer = Dense(2, 1, LINEAR, random.Random(0))
    layer.weights = [[1.0], [1.0]]
    layer.biases = [0.0]
    layer.forward([1.0, 1.0])
    _, grad_weights, grad_biases = layer.backward([1.0])
    layer.apply_gradients(grad_weights, grad_biases, learning_rate=0.1)
    # weights should have moved by exactly -lr * grad
    assert layer.weights[0][0] == 1.0 - 0.1 * grad_weights[0][0]
    assert layer.biases[0] == 0.0 - 0.1 * grad_biases[0]


def test_different_seeds_give_different_initial_weights():
    a = Dense(4, 4, RELU, random.Random(1))
    b = Dense(4, 4, RELU, random.Random(2))
    assert a.weights != b.weights


def test_weights_initialized_within_reasonable_bounds():
    layer = Dense(100, 10, RELU, random.Random(0))
    scale = 1.0 / (100 ** 0.5)
    for row in layer.weights:
        for w in row:
            assert -scale <= w <= scale
