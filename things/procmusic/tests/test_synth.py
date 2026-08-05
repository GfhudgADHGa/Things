import math

from procmusic.synth import (
    apply_adsr,
    mix,
    render_note,
    sawtooth_wave,
    silence,
    sine_wave,
    square_wave,
    triangle_wave,
)

SAMPLE_RATE = 44100


def _estimate_frequency(samples, sample_rate):
    """Counts sign changes (2 per full cycle for all our waveforms, since
    each one crosses zero going up once and going down once per period) to
    estimate frequency without needing an FFT or any dependency.
    """
    crossings = 0
    for i in range(1, len(samples)):
        if (samples[i - 1] < 0) != (samples[i] < 0):
            crossings += 1
    duration = len(samples) / sample_rate
    return crossings / 2 / duration


def test_sine_wave_length():
    samples = sine_wave(440, 1.0, SAMPLE_RATE)
    assert len(samples) == SAMPLE_RATE


def test_sine_wave_amplitude_bounds():
    samples = sine_wave(440, 1.0, SAMPLE_RATE, amplitude=0.7)
    assert max(samples) <= 0.7 + 1e-9
    assert min(samples) >= -0.7 - 1e-9
    assert max(samples) > 0.6  # actually reaches near peak somewhere


def test_sine_wave_frequency_via_zero_crossings():
    freq = _estimate_frequency(sine_wave(440, 2.0, SAMPLE_RATE), SAMPLE_RATE)
    assert abs(freq - 440) < 3


def test_square_wave_frequency_via_zero_crossings():
    freq = _estimate_frequency(square_wave(220, 2.0, SAMPLE_RATE), SAMPLE_RATE)
    assert abs(freq - 220) < 3


def test_square_wave_only_takes_two_values():
    samples = square_wave(100, 0.1, SAMPLE_RATE, amplitude=0.5)
    assert set(samples) == {0.5, -0.5}


def test_sawtooth_wave_frequency_via_zero_crossings():
    freq = _estimate_frequency(sawtooth_wave(330, 2.0, SAMPLE_RATE), SAMPLE_RATE)
    assert abs(freq - 330) < 3


def test_sawtooth_wave_is_monotonic_within_one_cycle():
    period_samples = int(SAMPLE_RATE / 100)
    samples = sawtooth_wave(100, 1.0, SAMPLE_RATE)
    one_cycle = samples[:period_samples]
    assert all(one_cycle[i] <= one_cycle[i + 1] for i in range(len(one_cycle) - 1))


def test_triangle_wave_frequency_via_zero_crossings():
    freq = _estimate_frequency(triangle_wave(550, 2.0, SAMPLE_RATE), SAMPLE_RATE)
    assert abs(freq - 550) < 3


def test_triangle_wave_amplitude_bounds():
    samples = triangle_wave(200, 1.0, SAMPLE_RATE, amplitude=1.0)
    assert max(samples) <= 1.0 + 1e-9
    assert min(samples) >= -1.0 - 1e-9


def test_adsr_starts_near_zero_and_rises_to_peak():
    n = 44100
    samples = [1.0] * n
    enveloped = apply_adsr(samples, SAMPLE_RATE, attack=0.1, decay=0.1, sustain_level=0.5, release=0.1)
    assert enveloped[0] < 0.05
    attack_end = int(0.1 * SAMPLE_RATE)
    assert enveloped[attack_end - 1] > 0.9


def test_adsr_settles_at_sustain_level():
    n = 44100
    samples = [1.0] * n
    enveloped = apply_adsr(samples, SAMPLE_RATE, attack=0.05, decay=0.05, sustain_level=0.4, release=0.05)
    mid_index = n // 2
    assert math.isclose(enveloped[mid_index], 0.4, abs_tol=0.01)


def test_adsr_releases_to_near_zero_at_end():
    n = 44100
    samples = [1.0] * n
    enveloped = apply_adsr(samples, SAMPLE_RATE, attack=0.05, decay=0.05, sustain_level=0.6, release=0.2)
    assert enveloped[-1] < 0.05


def test_adsr_output_same_length_as_input():
    n = 12345
    samples = [1.0] * n
    enveloped = apply_adsr(samples, SAMPLE_RATE, 0.01, 0.01, 0.5, 0.01)
    assert len(enveloped) == n


def test_adsr_handles_very_short_note_without_crashing():
    samples = [1.0] * 10  # shorter than a single envelope stage in samples
    enveloped = apply_adsr(samples, SAMPLE_RATE, 0.1, 0.1, 0.5, 0.1)
    assert len(enveloped) == 10


def test_mix_sums_overlapping_tracks():
    a = [0.1, 0.2, 0.3]
    b = [0.1, 0.1, 0.1]
    result = mix(a, b)
    assert result == [0.2, 0.30000000000000004, 0.4]


def test_mix_pads_shorter_tracks_with_zero():
    a = [1.0, 1.0, 1.0, 1.0]
    b = [1.0]
    result = mix(a, b)
    assert result == [2.0, 1.0, 1.0, 1.0]


def test_mix_of_no_tracks_is_empty():
    assert mix() == []


def test_silence_is_all_zero_and_correct_length():
    samples = silence(0.5, SAMPLE_RATE)
    assert len(samples) == SAMPLE_RATE // 2
    assert all(s == 0.0 for s in samples)


def test_render_note_length_matches_duration():
    samples = render_note(440, 0.5, SAMPLE_RATE)
    assert len(samples) == int(0.5 * SAMPLE_RATE)


def test_render_note_respects_amplitude():
    quiet = render_note(440, 0.3, SAMPLE_RATE, amplitude=0.1)
    loud = render_note(440, 0.3, SAMPLE_RATE, amplitude=0.9)
    assert max(abs(s) for s in loud) > max(abs(s) for s in quiet)
