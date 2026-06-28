"""Telemetry decoder + controller tests."""

import struct
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from alpha.telemetry_decoder import (
    TelemetryDecoder,
    SensorType,
    encode_frame,
    crc16_ccitt,
)
from omega.telemetry_controller import TelemetryController, Threshold, SensorHealth


def test_crc16():
    data = b"Hello, SpaceX!"
    crc = crc16_ccitt(data)
    assert isinstance(crc, int)
    assert 0 <= crc <= 0xFFFF


def test_encode_decode_frame():
    sensors = [
        (1, SensorType.PRESSURE, 100, 350.5),
        (2, SensorType.TEMPERATURE, 100, 933.15),
        (3, SensorType.ACCELERATION, 100, 9.81),
    ]
    frame = encode_frame(src=1, dst=2, seq=0, sensors=sensors)
    assert frame[:2] == b"\x1a\xcf"

    decoder = TelemetryDecoder()
    readings = decoder.feed(frame)
    assert len(readings) == 3
    assert readings[0].sensor_id == 1
    assert readings[0].sensor_type == SensorType.PRESSURE
    assert abs(readings[0].value - 350.5) < 0.01
    assert decoder.stats.decoded_frames == 1


def test_frame_loss_detection():
    decoder = TelemetryDecoder()
    frame0 = encode_frame(1, 2, 0, [(1, SensorType.PRESSURE, 100, 100.0)])
    frame2 = encode_frame(1, 2, 2, [(1, SensorType.PRESSURE, 100, 200.0)])

    decoder.feed(frame0)
    assert decoder.stats.dropped_frames == 0

    decoder.feed(frame2)
    assert decoder.stats.dropped_frames == 1
    assert decoder.stats.gap_count == 1


def test_crc_rejection():
    frame = encode_frame(1, 2, 0, [(1, SensorType.PRESSURE, 100, 100.0)])
    corrupted = bytearray(frame)
    corrupted[-1] ^= 0xFF

    decoder = TelemetryDecoder()
    readings = decoder.feed(bytes(corrupted))
    assert len(readings) == 0
    assert decoder.stats.crc_errors == 1


def test_buffered_decode():
    decoder = TelemetryDecoder()
    frame = encode_frame(1, 2, 0, [(1, SensorType.PRESSURE, 100, 42.0)])

    half = len(frame) // 2
    decoder.feed(frame[:half])
    assert len(decoder._readings) == 0

    decoder.feed(frame[half:])
    assert len(decoder._readings) == 1


def test_callback():
    decoder = TelemetryDecoder()
    received = []
    decoder.register_callback(lambda r: received.append(r))

    frame = encode_frame(1, 2, 0, [(1, SensorType.VOLTAGE, 100, 28.0)])
    decoder.feed(frame)
    assert len(received) == 1
    assert received[0].value == 28.0


def test_threshold_alerts():
    controller = TelemetryController()
    controller.add_threshold(
        Threshold(SensorType.TEMPERATURE, min_val=200.0, max_val=400.0, consecutive_breaches=2)
    )

    alerts = []
    controller.register_alert_callback(lambda a: alerts.append(a))

    frame = encode_frame(1, 2, 0, [(1, SensorType.TEMPERATURE, 100, 500.0)])
    controller.feed(frame)
    assert len(alerts) == 0

    frame2 = encode_frame(1, 2, 1, [(1, SensorType.TEMPERATURE, 100, 500.0)])
    controller.feed(frame2)
    assert len(alerts) == 1
    assert alerts[0].severity == "WARNING"


def test_ring_buffer_query():
    controller = TelemetryController()
    for i in range(5):
        frame = encode_frame(1, 2, i, [(1, SensorType.PRESSURE, 100, float(i * 10))])
        controller.feed(frame)

    results = controller.query_history(sensor_id=1, limit=3)
    assert len(results) == 3
    assert results[0].value == 40.0


def test_sensor_health():
    controller = TelemetryController()
    for i in range(10):
        frame = encode_frame(1, 2, i, [(1, SensorType.ACCELERATION, 100, 9.81 + i * 0.1)])
        controller.feed(frame)

    health = controller.get_sensor_health(1)
    assert health is not None
    assert health.mean > 9.0
    assert health.rate_of_change != 0.0


def test_pipeline_stats():
    controller = TelemetryController()
    frame = encode_frame(1, 2, 0, [(1, SensorType.PRESSURE, 100, 100.0)])
    controller.feed(frame)

    stats = controller.pipeline_stats
    assert stats["total_readings"] == 1
    assert stats["unique_sensors"] == 1
    assert stats["decoder_stats"]["health"] == "NOMINAL"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
