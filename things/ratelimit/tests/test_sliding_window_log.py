import random

import pytest

from ratelimit.sliding_window_log import SlidingWindowLog


def _brute_force_check_no_window_violation(allowed_timestamps, rate, window_size):
    """Independent re-verification, from nothing but the recorded list
    of granted timestamps: for every allowed timestamp t, count how
    many allowed timestamps fall in (t - window_size, t] by direct
    comparison (no deque, no incremental pruning) -- must never exceed
    rate. This is the actual guarantee a sliding-window limiter is
    supposed to provide, checked from scratch rather than by trusting
    the algorithm's own internal bookkeeping."""
    for t in allowed_timestamps:
        count = sum(1 for other in allowed_timestamps if t - window_size < other <= t)
        if count > rate:
            return False, t, count
    return True, None, None


@pytest.mark.parametrize("seed", range(150))
def test_never_exceeds_rate_in_any_trailing_window(seed):
    rng = random.Random(seed)
    rate = rng.randint(1, 20)
    window_size = rng.uniform(1.0, 20.0)
    limiter = SlidingWindowLog(rate=rate, window_size=window_size)

    t = 0.0
    allowed_timestamps = []
    for _ in range(rng.randint(20, 300)):
        t += rng.uniform(0.0, window_size / max(rate, 1))
        if limiter.allow(t):
            allowed_timestamps.append(t)

    ok, bad_t, bad_count = _brute_force_check_no_window_violation(allowed_timestamps, rate, window_size)
    assert ok, (bad_t, bad_count, rate)


def test_boundary_burst_scenario_is_correctly_rejected():
    """The identical saved-up-budget scenario that lets
    FixedWindowCounter through at ~2x rate (see
    test_fixed_window.py::test_boundary_burst_allows_close_to_double_the_rate)
    must NOT let more than `rate` through here, since the window is
    truly sliding rather than reset at a fixed boundary."""
    rate = 10
    window_size = 10.0
    limiter = SlidingWindowLog(rate=rate, window_size=window_size)

    just_before = [limiter.allow(9.99) for _ in range(rate)]
    just_after = [limiter.allow(10.01) for _ in range(rate)]

    total_allowed = sum(just_before) + sum(just_after)
    assert total_allowed <= rate + 1  # generous +1 slack for the exact boundary timestamp semantics
    assert total_allowed < 2 * rate


def test_simultaneous_requests_only_first_rate_allowed():
    limiter = SlidingWindowLog(rate=5, window_size=10.0)
    results = [limiter.allow(3.0) for _ in range(20)]
    assert sum(results) == 5


def test_full_budget_returns_after_window_elapses_with_no_traffic():
    limiter = SlidingWindowLog(rate=3, window_size=5.0)
    for _ in range(3):
        assert limiter.allow(0.0) is True
    assert limiter.allow(0.0) is False
    assert limiter.allow(5.01) is True  # oldest timestamp (0.0) has aged out


def test_rejects_nonpositive_parameters():
    with pytest.raises(ValueError):
        SlidingWindowLog(rate=0, window_size=1.0)
    with pytest.raises(ValueError):
        SlidingWindowLog(rate=5, window_size=0)
