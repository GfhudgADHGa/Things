import math

from neuralnet.losses import BINARY_CROSS_ENTROPY, MSE


def test_mse_zero_for_perfect_prediction():
    assert MSE.forward([1.0, 2.0], [1.0, 2.0]) == 0.0


def test_mse_matches_manual_computation():
    pred = [1.0, 3.0]
    target = [0.0, 1.0]
    expected = ((1.0 - 0.0) ** 2 + (3.0 - 1.0) ** 2) / 2
    assert math.isclose(MSE.forward(pred, target), expected)


def test_mse_gradient_matches_known_formula():
    pred = [2.0]
    target = [0.5]
    grad = MSE.backward(pred, target)
    assert math.isclose(grad[0], 2.0 * (2.0 - 0.5) / 1)


def test_mse_gradient_zero_at_perfect_prediction():
    grad = MSE.backward([1.0, 1.0], [1.0, 1.0])
    assert grad == [0.0, 0.0]


def test_bce_zero_for_confident_correct_prediction():
    loss = BINARY_CROSS_ENTROPY.forward([0.999999], [1.0])
    assert loss < 1e-4


def test_bce_large_for_confident_wrong_prediction():
    loss = BINARY_CROSS_ENTROPY.forward([0.0001], [1.0])
    assert loss > 5.0


def test_bce_does_not_raise_on_exact_zero_or_one_predictions():
    # naive log(0) would raise; clipping should prevent that
    BINARY_CROSS_ENTROPY.forward([0.0], [1.0])
    BINARY_CROSS_ENTROPY.forward([1.0], [0.0])


def test_bce_gradient_sign_points_toward_target():
    # prediction too low for target=1 -> gradient should be negative
    # (moving prediction up decreases loss)
    grad = BINARY_CROSS_ENTROPY.backward([0.2], [1.0])
    assert grad[0] < 0
    # prediction too high for target=0 -> gradient should be positive
    grad2 = BINARY_CROSS_ENTROPY.backward([0.8], [0.0])
    assert grad2[0] > 0
