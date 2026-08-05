import math

from neuralnet.activations import LINEAR, RELU, SIGMOID, TANH


def test_sigmoid_bounds_and_midpoint():
    assert math.isclose(SIGMOID.forward(0.0), 0.5)
    assert 0.0 < SIGMOID.forward(-100) < 1e-10
    assert SIGMOID.forward(100) > 1 - 1e-10


def test_sigmoid_is_numerically_stable_for_large_magnitude_input():
    # a naive 1/(1+exp(-x)) overflows for very negative x; must not raise
    # or produce nan/inf
    assert SIGMOID.forward(-1000) == 0.0
    assert SIGMOID.forward(1000) == 1.0


def test_sigmoid_derivative_matches_known_formula():
    y = SIGMOID.forward(0.7)
    assert math.isclose(SIGMOID.derivative_from_output(y), y * (1 - y))


def test_relu_zeroes_negatives_passes_positives():
    assert RELU.forward(-5) == 0.0
    assert RELU.forward(5) == 5.0
    assert RELU.forward(0) == 0.0


def test_relu_derivative():
    assert RELU.derivative_from_output(5.0) == 1.0
    assert RELU.derivative_from_output(0.0) == 0.0


def test_tanh_bounds_and_midpoint():
    assert TANH.forward(0.0) == 0.0
    assert -1.0 < TANH.forward(-10) < -0.99
    assert 0.99 < TANH.forward(10) < 1.0


def test_tanh_derivative_matches_known_formula():
    y = TANH.forward(0.4)
    assert math.isclose(TANH.derivative_from_output(y), 1 - y * y)


def test_linear_is_identity():
    assert LINEAR.forward(3.7) == 3.7
    assert LINEAR.derivative_from_output(999) == 1.0
