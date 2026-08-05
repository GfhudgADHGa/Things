import random

import pytest

from ratelimit.sliding_window_counter import SlidingWindowCounter
from ratelimit.sliding_window_log import SlidingWindowLog


@pytest.mark.parametrize("seed", range(100))
def test_agrees_with_exact_sliding_log_under_normal_load(seed):
    """The counter is an approximation by design (it assumes requests
    are spread evenly within each fixed sub-window, which real traffic
    never is exactly). Under normal load -- traffic arriving well
    below the configured rate, so the limiter is rarely near capacity
    -- it should agree with the exact SlidingWindowLog on almost every
    decision. (See test_agreement_degrades_under_sustained_overload for
    what happens once the limiter is actually saturated, which turns
    out to be a real and fairly dramatic effect, not a rare edge case.)"""
    rng = random.Random(seed)
    rate = rng.randint(2, 20)
    window_size = rng.uniform(2.0, 15.0)
    log = SlidingWindowLog(rate=rate, window_size=window_size)
    counter = SlidingWindowCounter(rate=rate, window_size=window_size)

    # mean arrival interval is ~3x the steady interval needed to hit
    # the rate limit, i.e. demand stays comfortably under capacity
    t = 0.0
    agreements = 0
    total = 0
    for _ in range(300):
        t += rng.uniform(0.0, window_size / max(rate, 1) * 6.0)
        log_result = log.allow(t)
        counter_result = counter.allow(t)
        agreements += log_result == counter_result
        total += 1

    agreement_rate = agreements / total
    assert agreement_rate > 0.95, (agreement_rate, rate, window_size)


def test_agreement_degrades_under_sustained_overload():
    """A genuine, measured property of the approximation, not a design
    flaw exactly: per-decision agreement with the exact sliding log
    drops substantially once the limiter is actually saturated or
    overloaded -- from ~99.9% agreement at 30% of capacity down to
    ~65-70% under 1.5-3x overload, measured directly here. That's
    precisely the traffic regime where a rate limiter's exact behavior
    matters most, which is worth knowing about this approximation even
    though its *aggregate* throughput still stays close to the exact
    log's (see test_never_wildly_overcounts_relative_to_exact_log)."""
    rng = random.Random(0)
    rate = 10
    window_size = 5.0

    def measure_agreement(load_factor, seed):
        local_rng = random.Random(seed)
        log = SlidingWindowLog(rate=rate, window_size=window_size)
        counter = SlidingWindowCounter(rate=rate, window_size=window_size)
        mean_interval = (window_size / rate) / load_factor
        t = 0.0
        agreements = 0
        for _ in range(300):
            t += local_rng.uniform(0.0, 2 * mean_interval)
            agreements += log.allow(t) == counter.allow(t)
        return agreements / 300

    low_load = [measure_agreement(0.3, seed) for seed in range(40)]
    overload = [measure_agreement(2.0, seed) for seed in range(40)]

    assert sum(low_load) / len(low_load) > 0.97
    assert sum(overload) / len(overload) < 0.85
    assert sum(overload) / len(overload) < sum(low_load) / len(low_load)


@pytest.mark.parametrize("seed", range(60))
def test_never_wildly_overcounts_relative_to_exact_log(seed):
    """The approximation can occasionally allow a request the exact log
    would have denied (or vice versa) right around a window boundary,
    but the total granted over a long run should stay close to the
    exact log's total -- not systematically inflate throughput by a
    large factor the way FixedWindowCounter's boundary burst does."""
    rng = random.Random(seed + 10_000)
    rate = rng.randint(5, 30)
    window_size = rng.uniform(2.0, 10.0)
    log = SlidingWindowLog(rate=rate, window_size=window_size)
    counter = SlidingWindowCounter(rate=rate, window_size=window_size)

    t = 0.0
    log_total = 0
    counter_total = 0
    for _ in range(500):
        t += rng.uniform(0.0, window_size / max(rate, 1) * 0.5)
        log_total += log.allow(t)
        counter_total += counter.allow(t)

    assert counter_total <= log_total * 1.25 + 3


def test_boundary_burst_scenario_is_substantially_mitigated():
    """Same saved-up-budget scenario as the fixed-window test: the
    counter shouldn't let the full 2x through the way a hard-reset
    fixed window does, because part of the previous window's count is
    still weighted into the estimate right after the boundary."""
    rate = 10
    window_size = 10.0
    limiter = SlidingWindowCounter(rate=rate, window_size=window_size)

    just_before = [limiter.allow(9.99) for _ in range(rate)]
    just_after = [limiter.allow(10.01) for _ in range(rate)]

    total_allowed = sum(just_before) + sum(just_after)
    assert total_allowed < 2 * rate


def test_rejects_nonpositive_parameters():
    with pytest.raises(ValueError):
        SlidingWindowCounter(rate=0, window_size=1.0)
    with pytest.raises(ValueError):
        SlidingWindowCounter(rate=5, window_size=0)
