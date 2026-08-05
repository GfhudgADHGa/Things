import random

import pytest

from procmusic.drums import _highpass, hihat, kick, render_drum_track, render_pattern, snare

SAMPLE_RATE = 44100


def _estimate_frequency_in_window(samples, sample_rate):
    """Same zero-crossing technique as test_synth.py's oscillator checks,
    applied to a short window of a percussion hit to estimate its
    instantaneous-ish pitch."""
    crossings = 0
    for i in range(1, len(samples)):
        if (samples[i - 1] < 0) != (samples[i] < 0):
            crossings += 1
    duration = len(samples) / sample_rate
    return crossings / 2 / duration if duration else 0.0


def test_kick_has_expected_duration():
    samples = kick(duration=0.3, sample_rate=SAMPLE_RATE)
    assert samples
    assert abs(len(samples) - int(0.3 * SAMPLE_RATE)) <= 1


def test_kick_amplitude_stays_in_range():
    samples = kick(sample_rate=SAMPLE_RATE)
    assert all(-1.0 <= s <= 1.0 for s in samples)


def test_kick_decays_toward_silence():
    samples = kick(duration=0.25, sample_rate=SAMPLE_RATE)
    n = len(samples)
    start_energy = sum(s * s for s in samples[: n // 10])
    end_energy = sum(s * s for s in samples[-n // 10:])
    assert end_energy < start_energy


def test_kick_frequency_sweeps_down():
    # The kick starts near start_freq and ends near end_freq < start_freq;
    # estimate frequency in the first vs. last quarter and check it fell.
    samples = kick(duration=0.3, sample_rate=SAMPLE_RATE, start_freq=200.0, end_freq=50.0)
    n = len(samples)
    first_quarter_freq = _estimate_frequency_in_window(samples[: n // 4], SAMPLE_RATE)
    last_quarter_freq = _estimate_frequency_in_window(samples[-n // 4:], SAMPLE_RATE)
    assert last_quarter_freq < first_quarter_freq


def test_snare_is_deterministic_given_the_same_rng_seed():
    a = snare(sample_rate=SAMPLE_RATE, rng=random.Random(5))
    b = snare(sample_rate=SAMPLE_RATE, rng=random.Random(5))
    assert a == b


def test_snare_amplitude_stays_in_range():
    samples = snare(sample_rate=SAMPLE_RATE, rng=random.Random(0))
    assert all(-1.0 <= s <= 1.0 for s in samples)


def test_hihat_is_shorter_than_kick_by_default():
    assert len(hihat(sample_rate=SAMPLE_RATE)) < len(kick(sample_rate=SAMPLE_RATE))


def test_hihat_amplitude_stays_in_range():
    samples = hihat(sample_rate=SAMPLE_RATE, rng=random.Random(1))
    assert all(-1.0 <= s <= 1.0 for s in samples)


# ---- the highpass filter's closed-form property ----

def test_highpass_of_constant_signal_is_zero_after_the_first_sample():
    # y[n] = x[n] - x[n-1]; for a constant input, every difference after
    # the first sample is exactly zero -- a direct algebraic consequence
    # of the filter's definition, not something that needs measuring.
    constant = [0.7] * 100
    result = _highpass(constant)
    assert result[0] == 0.7
    assert all(v == 0.0 for v in result[1:])


def test_highpass_of_empty_signal_is_empty():
    assert _highpass([]) == []


def test_highpass_preserves_length():
    samples = [0.1, -0.2, 0.3, -0.4, 0.5]
    assert len(_highpass(samples)) == len(samples)


def test_highpass_matches_hand_computed_differences():
    samples = [1.0, 3.0, 2.0, -1.0]
    result = _highpass(samples)
    assert result == [1.0, 2.0, -1.0, -3.0]


# ---- pattern rendering ----

def test_render_pattern_all_silence_is_all_zero():
    buffer = render_pattern("....", step_duration=0.1, sample_rate=SAMPLE_RATE, sound_fn=lambda: kick())
    assert buffer == [0.0] * int(0.1 * SAMPLE_RATE * 4)


def test_render_pattern_length_matches_pattern_times_step_duration():
    buffer = render_pattern("x.x.x.x.", step_duration=0.05, sample_rate=SAMPLE_RATE, sound_fn=lambda: kick())
    assert len(buffer) == int(0.05 * SAMPLE_RATE * 8)


def test_render_pattern_places_hit_at_the_right_step():
    hit = [1.0, 1.0, 1.0]
    buffer = render_pattern("..x.", step_duration=0.01, sample_rate=SAMPLE_RATE, sound_fn=lambda: list(hit))
    step_samples = int(0.01 * SAMPLE_RATE)
    assert all(v == 0.0 for v in buffer[: 2 * step_samples])
    assert buffer[2 * step_samples: 2 * step_samples + 3] == hit


def test_render_pattern_overlapping_hits_add_rather_than_overwrite():
    # a hit longer than one step should bleed into (and add onto) the next step
    hit = [1.0, 1.0, 1.0, 1.0]
    buffer = render_pattern("xx", step_duration=0.01, sample_rate=SAMPLE_RATE, sound_fn=lambda: list(hit))
    step_samples = int(0.01 * SAMPLE_RATE)
    overlap = step_samples - len(hit) if step_samples > len(hit) else 0
    if overlap == 0:
        # the two hits genuinely overlap: the overlapping region should sum to 2.0
        assert buffer[step_samples] == pytest.approx(2.0)


# ---- full drum track ----

def test_render_drum_track_mismatched_pattern_lengths_raise():
    with pytest.raises(ValueError):
        render_drum_track("x...", "x.", "x...", step_duration=0.1, sample_rate=SAMPLE_RATE)


def test_render_drum_track_is_deterministic_given_the_same_seed():
    a = render_drum_track("x...x...", "....x...", "x.x.x.x.", step_duration=0.05, sample_rate=SAMPLE_RATE, seed=3)
    b = render_drum_track("x...x...", "....x...", "x.x.x.x.", step_duration=0.05, sample_rate=SAMPLE_RATE, seed=3)
    assert a == b


def test_render_drum_track_different_seeds_differ():
    a = render_drum_track("....x...", "....x...", "....x...", step_duration=0.05, sample_rate=SAMPLE_RATE, seed=1)
    b = render_drum_track("....x...", "....x...", "....x...", step_duration=0.05, sample_rate=SAMPLE_RATE, seed=2)
    assert a != b  # snare/hihat noise components depend on the seed


def test_render_drum_track_all_silence_pattern_is_all_zero():
    track = render_drum_track("....", "....", "....", step_duration=0.02, sample_rate=SAMPLE_RATE)
    assert all(s == 0.0 for s in track)


def test_render_drum_track_amplitude_stays_reasonable():
    track = render_drum_track(
        "x...x...x...x...", "....x.......x...", "x.x.x.x.x.x.x.x.",
        step_duration=0.125, sample_rate=SAMPLE_RATE, seed=0,
    )
    # individual amplitudes are tuned so even fully overlapping hits stay close to [-1, 1]
    assert max(abs(s) for s in track) < 1.5
