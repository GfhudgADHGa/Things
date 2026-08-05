import random

import pytest

from ratelimit.fixed_window import FixedWindowCounter


def test_exactly_rate_allowed_within_one_saturated_window():
    limiter = FixedWindowCounter(rate=5, window_size=10.0)
    results = [limiter.allow(1.0) for _ in range(20)]
    assert sum(results) == 5


def test_resets_hard_at_window_boundary():
    limiter = FixedWindowCounter(rate=3, window_size=10.0)
    for _ in range(3):
        assert limiter.allow(5.0) is True
    assert limiter.allow(5.0) is False
    # new window starts at t=10.0
    assert limiter.allow(10.0) is True


@pytest.mark.parametrize("seed", range(100))
def test_total_allowed_in_one_window_never_exceeds_rate_regardless_of_arrival_pattern(seed):
    rng = random.Random(seed)
    rate = rng.randint(1, 30)
    window_size = rng.uniform(1.0, 20.0)
    limiter = FixedWindowCounter(rate=rate, window_size=window_size)
    n_requests = rng.randint(1, 100)
    times = sorted(rng.uniform(0.0, window_size * 0.999) for _ in range(n_requests))
    allowed = sum(1 for t in times if limiter.allow(t))
    assert allowed == min(rate, n_requests)


def test_boundary_burst_allows_close_to_double_the_rate():
    """The known structural flaw: `rate` requests saved up for just
    before a window boundary, plus `rate` more right after it, both
    land within a much shorter real time span than window_size -- so a
    client can get roughly 2x its supposed budget through in a tight
    window straddling the boundary. This isn't a bug in this
    implementation; it's demonstrated here as an inherent property of
    resetting a hard counter at fixed points in time, and contrasted
    against sliding_window_log's handling of the identical scenario in
    test_sliding_window_log.py."""
    rate = 10
    window_size = 10.0
    limiter = FixedWindowCounter(rate=rate, window_size=window_size)

    # rate requests right at the end of window [0, 10)
    just_before = [limiter.allow(9.99) for _ in range(rate)]
    # rate requests right at the start of window [10, 20)
    just_after = [limiter.allow(10.01) for _ in range(rate)]

    total_allowed = sum(just_before) + sum(just_after)
    # a real span of only 0.02s let through the full 2x rate
    assert total_allowed == 2 * rate


def test_rejects_nonpositive_parameters():
    with pytest.raises(ValueError):
        FixedWindowCounter(rate=0, window_size=1.0)
    with pytest.raises(ValueError):
        FixedWindowCounter(rate=5, window_size=0)
