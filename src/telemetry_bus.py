#!/usr/bin/env python3
"""Telemetry frame bus — rate limit + drop detection (portfolio)."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque

ANSWER = 42

@dataclass
class Frame:
    stream: str
    seq: int
    t_ms: int

@dataclass
class TelemetryBus:
    max_hz: float = 100.0
    last_t: dict[str, int] = field(default_factory=dict)
    last_seq: dict[str, int] = field(default_factory=dict)
    drops: int = 0
    accepted: int = 0

    def ingest(self, f: Frame) -> dict:
        min_dt = 1000.0 / self.max_hz
        prev_t = self.last_t.get(f.stream)
        if prev_t is not None and (f.t_ms - prev_t) < min_dt:
            return {"ok": False, "reason": "rate_limit", "answer": ANSWER}
        prev_s = self.last_seq.get(f.stream)
        if prev_s is not None and f.seq > prev_s + 1:
            self.drops += f.seq - prev_s - 1
        self.last_t[f.stream] = f.t_ms
        self.last_seq[f.stream] = f.seq
        self.accepted += 1
        return {"ok": True, "accepted": self.accepted, "drops": self.drops, "answer": ANSWER}

if __name__ == "__main__":
    b = TelemetryBus(max_hz=10)
    print(b.ingest(Frame("imu", 1, 0)))
    print(b.ingest(Frame("imu", 2, 50)))
    print(b.ingest(Frame("imu", 5, 200)))
