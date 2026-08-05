import random

from neuralnet.activations import LINEAR, SIGMOID, TANH
from neuralnet.layer import Dense
from neuralnet.losses import MSE
from neuralnet.network import Sequential


def test_forward_chains_layers():
    net = Sequential([Dense(2, 3, TANH, random.Random(0)), Dense(3, 1, SIGMOID, random.Random(0))])
    y = net.forward([0.5, -0.5])
    assert len(y) == 1
    assert 0.0 <= y[0] <= 1.0


def test_train_step_reduces_loss_on_a_single_example():
    rng = random.Random(0)
    net = Sequential([Dense(2, 4, TANH, rng), Dense(4, 1, SIGMOID, rng)])
    x, y = [0.3, 0.7], [1.0]

    loss_before = MSE.forward(net.forward(x), y)
    for _ in range(50):
        net.train_step(x, y, MSE, learning_rate=0.5)
    loss_after = MSE.forward(net.forward(x), y)

    assert loss_after < loss_before


def test_network_learns_xor():
    rng = random.Random(1)
    net = Sequential([Dense(2, 8, TANH, rng), Dense(8, 1, SIGMOID, rng)])
    dataset = [
        ([0.0, 0.0], [0.0]),
        ([0.0, 1.0], [1.0]),
        ([1.0, 0.0], [1.0]),
        ([1.0, 1.0], [0.0]),
    ]

    for _ in range(3000):
        net.train_epoch(dataset, MSE, learning_rate=0.5)

    for x, y in dataset:
        pred = net.forward(x)[0]
        assert round(pred) == y[0], f"{x} -> {pred}, expected {y[0]}"


def test_train_epoch_returns_average_loss():
    rng = random.Random(0)
    net = Sequential([Dense(1, 1, LINEAR, rng)])
    dataset = [([1.0], [1.0]), ([2.0], [2.0])]
    avg_loss = net.train_epoch(dataset, MSE, learning_rate=0.0)  # lr=0: no learning, just measuring
    manual_avg = (MSE.forward(net.forward([1.0]), [1.0]) + MSE.forward(net.forward([2.0]), [2.0])) / 2
    assert avg_loss == manual_avg


def test_zero_learning_rate_leaves_weights_unchanged():
    rng = random.Random(0)
    net = Sequential([Dense(2, 2, TANH, rng)])
    weights_before = [row[:] for row in net.layers[0].weights]
    net.train_step([0.5, 0.5], [1.0, 0.0], MSE, learning_rate=0.0)
    assert net.layers[0].weights == weights_before


def test_train_step_with_momentum_reduces_loss():
    rng = random.Random(0)
    net = Sequential([Dense(2, 4, TANH, rng), Dense(4, 1, SIGMOID, rng)])
    x, y = [0.3, 0.7], [1.0]

    loss_before = MSE.forward(net.forward(x), y)
    for _ in range(50):
        net.train_step(x, y, MSE, learning_rate=0.3, momentum=0.9)
    loss_after = MSE.forward(net.forward(x), y)

    assert loss_after < loss_before


def test_train_epoch_accepts_momentum_keyword():
    rng = random.Random(0)
    net = Sequential([Dense(1, 1, LINEAR, rng)])
    dataset = [([1.0], [1.0]), ([2.0], [2.0])]
    # just needs to not raise, and momentum=0 should match plain SGD's
    # untouched loss-averaging behavior
    avg_loss = net.train_epoch(dataset, MSE, learning_rate=0.0, momentum=0.5)
    manual_avg = (MSE.forward(net.forward([1.0]), [1.0]) + MSE.forward(net.forward([2.0]), [2.0])) / 2
    assert avg_loss == manual_avg
