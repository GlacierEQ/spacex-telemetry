"""Protobuf condensation must win on real multi-frame telemetry — not for show."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from proto_codec import (
    decode_batch,
    decode_frame,
    decode_helix_envelope,
    encode_batch,
    encode_frame,
    encode_helix_envelope,
    measure_condensation,
)
from telemetry_bus import Frame, TelemetryBus


class TestProtobufReal(unittest.TestCase):
    def test_roundtrip_frame(self):
        raw = encode_frame("imu", 42, 1000, b"\x01\x02", {"temp": 22.5})
        d = decode_frame(raw)
        self.assertEqual(d["stream"], "imu")
        self.assertEqual(d["seq"], 42)
        self.assertEqual(d["t_ms"], 1000)
        self.assertEqual(d["payload"], b"\x01\x02")
        self.assertAlmostEqual(d["metrics"]["temp"], 22.5)

    def test_batch_smaller_than_json(self):
        frames = [
            {"stream": "gnc", "seq": i, "t_ms": i * 5, "metrics": {"v": float(i % 7)}}
            for i in range(200)
        ]
        m = measure_condensation(frames)
        self.assertTrue(m["wins"], m)
        self.assertGreater(m["savings_pct"], 30.0, m)  # real condensation
        # round-trip
        blob = encode_batch(frames)
        back = decode_batch(blob)
        self.assertEqual(len(back["frames"]), 200)
        self.assertEqual(back["frames"][0]["stream"], "gnc")

    def test_bus_export_and_condense(self):
        bus = TelemetryBus(max_hz=100_000)
        for i in range(1, 151):
            r = bus.ingest(Frame(f"s{i % 3}", i, i * 2))
            self.assertTrue(r["ok"], r)
        blob = bus.export_protobuf_batch(source="unit")
        self.assertIsInstance(blob, (bytes, bytearray))
        self.assertGreater(len(blob), 20)
        report = bus.condensation_report()
        self.assertTrue(report["wins"], report)
        self.assertEqual(report["n_frames"], 150)
        # protobuf must beat JSON by a clear margin on this load
        self.assertLess(report["ratio_pb_over_json"], 0.7, report)

    def test_helix_envelope_roundtrip(self):
        raw = encode_helix_envelope(
            pair_id="flight",
            piston="orbital_leo",
            spiral="alpha",
            status="NOMINAL",
            numbers={"speed_m_s": 7669.0, "period_s": 5550.0},
            tags={"source": "test"},
        )
        d = decode_helix_envelope(raw)
        self.assertEqual(d["pair_id"], "flight")
        self.assertEqual(d["piston"], "orbital_leo")
        self.assertAlmostEqual(d["numbers"]["speed_m_s"], 7669.0)


if __name__ == "__main__":
    unittest.main()
