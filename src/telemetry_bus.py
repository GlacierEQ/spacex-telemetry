#!/usr/bin/env python3
"""Telemetry frame bus — rate limiting and sequence gap detection.

Production-minded portfolio module: clear metrics, no magic placeholders.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Frame:
    stream: str
    seq: int
    t_ms: int


@dataclass
class TelemetryBus:
    """Ingest frames with per-stream max rate and drop accounting.

    Accepted frames are kept for protobuf batch export (real wire condensation).
    """

    max_hz: float = 100.0
    last_t: dict[str, int] = field(default_factory=dict)
    last_seq: dict[str, int] = field(default_factory=dict)
    drops: int = 0
    accepted: int = 0
    rate_limited: int = 0
    keep_history: int = 10_000
    _per_stream_drops: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _history: list = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if self.max_hz <= 0:
            raise ValueError("max_hz must be > 0")

    def ingest(self, f: Frame) -> dict:
        if f.seq < 0 or f.t_ms < 0:
            return {"ok": False, "reason": "invalid_frame"}

        min_dt = 1000.0 / self.max_hz
        prev_t = self.last_t.get(f.stream)
        if prev_t is not None and (f.t_ms - prev_t) < min_dt - 1e-9:
            self.rate_limited += 1
            return {
                "ok": False,
                "reason": "rate_limit",
                "min_dt_ms": min_dt,
                "stream": f.stream,
            }

        prev_s = self.last_seq.get(f.stream)
        gap = 0
        if prev_s is not None and f.seq > prev_s + 1:
            gap = f.seq - prev_s - 1
            self.drops += gap
            self._per_stream_drops[f.stream] += gap
        elif prev_s is not None and f.seq <= prev_s:
            return {
                "ok": False,
                "reason": "replay_or_reorder",
                "stream": f.stream,
                "seq": f.seq,
                "last_seq": prev_s,
            }

        self.last_t[f.stream] = f.t_ms
        self.last_seq[f.stream] = f.seq
        self.accepted += 1
        self._history.append(f)
        if len(self._history) > self.keep_history:
            self._history = self._history[-self.keep_history :]
        return {
            "ok": True,
            "accepted": self.accepted,
            "drops": self.drops,
            "gap": gap,
            "stream": f.stream,
        }

    def export_protobuf_batch(self, *, source: str = "bus") -> bytes:
        """Serialize accepted history as protobuf TelemetryBatch (dense wire)."""
        from proto_codec import encode_batch

        return encode_batch(self._history, source=source)

    def condensation_report(self, *, source: str = "bus") -> dict:
        """Measured protobuf vs JSON size for current history."""
        from proto_codec import measure_condensation

        return measure_condensation(self._history, source=source)

    def stats(self) -> dict:
        return {
            "accepted": self.accepted,
            "drops": self.drops,
            "rate_limited": self.rate_limited,
            "streams": len(self.last_seq),
            "history": len(self._history),
            "per_stream_drops": dict(self._per_stream_drops),
        }


if __name__ == "__main__":
    b = TelemetryBus(max_hz=10)
    print(b.ingest(Frame("imu", 1, 0)))
    print(b.ingest(Frame("imu", 2, 50)))  # rate limited
    print(b.ingest(Frame("imu", 5, 200)))  # gap 2
    print(b.stats())
