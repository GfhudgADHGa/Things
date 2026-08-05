import math
import os

from procmusic.wav import read_wav, write_wav


def test_roundtrip_preserves_samples_within_16bit_quantization(tmp_path):
    samples = [math.sin(2 * math.pi * 440 * i / 44100) * 0.5 for i in range(1000)]
    path = str(tmp_path / "test.wav")
    write_wav(samples, path)
    read_back, sr = read_wav(path)

    assert sr == 44100
    assert len(read_back) == len(samples)
    for original, recovered in zip(samples, read_back):
        assert abs(original - recovered) < 1e-3  # 16-bit quantization tolerance


def test_wav_header_riff_and_wave_markers(tmp_path):
    path = str(tmp_path / "test.wav")
    write_wav([0.0] * 100, path)
    with open(path, "rb") as f:
        data = f.read(12)
    assert data[0:4] == b"RIFF"
    assert data[8:12] == b"WAVE"


def test_wav_file_size_matches_sample_count(tmp_path):
    path = str(tmp_path / "test.wav")
    n = 5000
    write_wav([0.0] * n, path)
    # 44-byte header + 2 bytes per 16-bit sample
    assert os.path.getsize(path) == 44 + n * 2


def test_clamping_out_of_range_samples(tmp_path):
    path = str(tmp_path / "test.wav")
    write_wav([2.0, -2.0, 0.0], path, sample_rate=44100)
    samples, _ = read_wav(path)
    assert samples[0] > 0.99  # clamped to (near) +1, not wrapped
    assert samples[1] < -0.99  # clamped to (near) -1, not wrapped
    assert abs(samples[2]) < 1e-3


def test_empty_samples_produces_valid_empty_wav(tmp_path):
    path = str(tmp_path / "test.wav")
    write_wav([], path)
    samples, sr = read_wav(path)
    assert samples == []
    assert sr == 44100


def test_custom_sample_rate_roundtrips(tmp_path):
    path = str(tmp_path / "test.wav")
    write_wav([0.1, 0.2, 0.3], path, sample_rate=22050)
    _, sr = read_wav(path)
    assert sr == 22050


def test_silence_produces_zero_samples(tmp_path):
    path = str(tmp_path / "test.wav")
    write_wav([0.0] * 100, path)
    samples, _ = read_wav(path)
    assert all(s == 0.0 for s in samples)
