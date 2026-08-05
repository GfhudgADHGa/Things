import random

import pytest

from ratelimit.token_bucket import TokenBucket


def test_initial_burst_up_to_capacity_all_allowed():
    bucket = TokenBucket(rate=1.0, capacity=10)
    results = [bucket.allow(0.0) for _ in range(10)]
    assert all(results)
    assert bucket.allow(0.0) is False  # 11th at the same instant: bucket empty


def test_denied_until_enough_time_passes_for_one_token():
    bucket = TokenBucket(rate=2.0, capacity=1)  # 1 token, refills at 2/sec
    assert bucket.allow(0.0) is True
    assert bucket.allow(0.1) is False  # only 0.2 tokens have regenerated
    assert bucket.allow(0.5) is True   # by t=0.5, 0.5*2=1.0 tokens available


@pytest.mark.parametrize("seed", range(100))
def test_never_exceeds_capacity_worth_of_requests_in_a_burst(seed):
    rng = random.Random(seed)
    capacity = rng.randint(1, 50)
    rate = rng.uniform(0.1, 20.0)
    bucket = TokenBucket(rate=rate, capacity=capacity)
    allowed = sum(1 for _ in range(capacity * 3) if bucket.allow(0.0))
    assert allowed == capacity


@pytest.mark.parametrize("seed", range(30))
def test_long_run_throughput_matches_configured_rate(seed):
    """Over a long enough run at a request arrival rate *much higher*
    than the bucket's refill rate, with gaps between arrivals kept tiny
    relative to 1/rate (so tokens essentially never have a chance to
    accumulate past capacity between requests -- see
    test_small_capacity_measurably_costs_throughput_when_demand_has_gaps
    for what happens when that assumption doesn't hold), the number of
    allowed requests should converge tightly to rate * duration."""
    rng = random.Random(seed + 10_000)
    rate = rng.uniform(5.0, 50.0)  # keep rate off the very low end: with a
    # fixed duration, small rate means a huge iteration count for no extra
    # statistical benefit, since what matters is duration * rate (total
    # expected grants), not the number of polling iterations itself
    capacity = rng.uniform(3.0, 20.0)
    duration = 500.0
    bucket = TokenBucket(rate=rate, capacity=capacity)

    t = 0.0
    allowed = 0
    while t < duration:
        if bucket.allow(t):
            allowed += 1
        t += rng.uniform(0.0, 1.0 / (rate * 20))

    expected = rate * duration
    tolerance = capacity * 3 + rate * 2
    assert abs(allowed - expected) < tolerance, (allowed, expected, tolerance)


@pytest.mark.parametrize("seed", range(40))
def test_small_capacity_measurably_costs_throughput_when_demand_has_gaps(seed):
    """A real, non-obvious consequence of what `capacity` means: tokens
    that accumulate *past* capacity while no request happens to be
    waiting are discarded, not banked -- that's the whole point of a
    capacity ceiling (it's what caps burst size). But it also means
    that when demand has any gaps at all and capacity is small (close
    to 1), realized long-run throughput measurably falls short of
    rate * duration, purely from that discarded refill -- not from
    anything resembling a bug. This test demonstrates it directly: a
    request stream with random idle gaps large enough to occasionally
    overflow a capacity-1 bucket loses real, measurable throughput,
    and that loss shrinks as capacity grows and there's more room to
    bank a temporary surplus."""
    rng = random.Random(seed + 20_000)
    rate = rng.uniform(2.0, 20.0)
    duration = 2000.0

    def simulate(capacity):
        bucket = TokenBucket(rate=rate, capacity=capacity)
        local_rng = random.Random(seed + 20_000)
        local_rng.uniform(2.0, 20.0)  # consume the same draw as `rate` above
        t = 0.0
        allowed = 0
        while t < duration:
            if bucket.allow(t):
                allowed += 1
            # gaps large enough to sometimes exceed several tokens'
            # worth of time, so a tiny capacity will clip real refill
            t += local_rng.uniform(0.0, 3.0 / rate)
        return allowed

    tiny_capacity_allowed = simulate(1.0)
    large_capacity_allowed = simulate(50.0)
    expected = rate * duration

    tiny_deficit = expected - tiny_capacity_allowed
    large_deficit = expected - large_capacity_allowed
    assert tiny_deficit > 0
    assert tiny_deficit > large_deficit


def test_rejects_nonpositive_parameters():
    with pytest.raises(ValueError):
        TokenBucket(rate=0, capacity=5)
    with pytest.raises(ValueError):
        TokenBucket(rate=5, capacity=0)
    with pytest.raises(ValueError):
        TokenBucket(rate=-1, capacity=5)


def test_rejects_time_going_backwards():
    bucket = TokenBucket(rate=1.0, capacity=5)
    bucket.allow(10.0)
    with pytest.raises(ValueError):
        bucket.allow(5.0)


def test_tokens_never_exceed_capacity_after_long_idle():
    bucket = TokenBucket(rate=100.0, capacity=5)
    bucket.allow(0.0)
    bucket.allow(1_000_000.0)  # huge idle gap
    assert bucket.tokens <= bucket.capacity
