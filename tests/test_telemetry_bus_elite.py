"""Elite tests for telemetry bus — rate, gap, replay."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from telemetry_bus import Frame, TelemetryBus


def test_accept_and_gap():
    b = TelemetryBus(max_hz=1000)
    assert b.ingest(Frame("imu", 1, 0))["ok"]
    r = b.ingest(Frame("imu", 4, 10))
    assert r["ok"]
    assert r["gap"] == 2
    assert b.drops == 2


def test_rate_limit():
    b = TelemetryBus(max_hz=10)
    assert b.ingest(Frame("s", 1, 0))["ok"]
    r = b.ingest(Frame("s", 2, 50))
    assert not r["ok"]
    assert r["reason"] == "rate_limit"


def test_replay_rejected():
    b = TelemetryBus(max_hz=1000)
    b.ingest(Frame("s", 5, 0))
    r = b.ingest(Frame("s", 5, 100))
    assert not r["ok"]
    assert r["reason"] == "replay_or_reorder"


def test_no_magic_answer():
    b = TelemetryBus()
    r = b.ingest(Frame("s", 1, 0))
    assert "answer" not in r
