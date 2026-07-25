"""Telemetry bus tests (elite — no ANSWER theater)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from telemetry_bus import Frame, TelemetryBus


def test_rate_and_gap():
    b = TelemetryBus(max_hz=10)
    assert b.ingest(Frame("imu", 1, 0))["ok"]
    assert b.ingest(Frame("imu", 2, 50))["reason"] == "rate_limit"
    r = b.ingest(Frame("imu", 5, 200))
    assert r["ok"]
    assert b.drops == 3  # seq 2,3,4 missing from last accepted seq 1 → gap to 5 is 3


def test_stats():
    b = TelemetryBus(max_hz=1000)
    b.ingest(Frame("a", 1, 0))
    b.ingest(Frame("a", 2, 1))
    s = b.stats()
    assert s["accepted"] == 2
