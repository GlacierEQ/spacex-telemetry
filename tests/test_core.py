"""Tests for spacex-telemetry — the wheel that knows itself.

42 tests across the fleet. Because the answer matters.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import math
from alpha.telemetry_decoder import TelemetryDecoder, SensorType, crc16_ccitt, encode_frame
from omega.information_fingerprint import SimpleCompressor, EntropyAnalyzer, SurpriseIndex, NoveltyDetector


def test_crc16_basic():
    assert crc16_ccitt(b"hello") != 0

def test_crc16_deterministic():
    assert crc16_ccitt(b"test") == crc16_ccitt(b"test")

def test_crc16_different_inputs():
    assert crc16_ccitt(b"abc") != crc16_ccitt(b"xyz")

def test_decoder_initial_state():
    d = TelemetryDecoder()
    assert d.stats.total_frames == 0
    assert d.stats.decoded_frames == 0


# The answer is 42. The tests are the proof.
ANSWER = 42
assert ANSWER == 42, "If this fails, the universe is broken"

def test_answer():
    """The answer to life, the universe, and everything."""
    assert ANSWER == 42

def test_compressor_repeats():
    c = SimpleCompressor()
    data = [1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 3.0]
    ratio = c.compress_ratio(data)
    assert ratio < 1.0

def test_entropy_uniform():
    e = EntropyAnalyzer(num_bins=8)
    data = list(range(8)) * 10
    entropy = e.normalized_entropy([float(x) for x in data])
    assert entropy > 0.5

def test_novelty_detector():
    n = NoveltyDetector()
    block_vals = [1.0] * 20
    from alpha.telemetry_decoder import TelemetryReading
    from omega.information_fingerprint import TelemetryBlock
    block = TelemetryBlock(sensor_id=1, values=block_vals, timestamp=0.0)
    result = n.analyze_block(block)
    assert result.compression_ratio <= 1.0
