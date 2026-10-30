#!/usr/bin/env python3
"""Concurrent-safe, bounded telemetry ingestion with atomic batch semantics.

The simulator maintains per-stream replay, gap and time-order invariants.
No externally authenticated or real spacecraft telemetry is implied.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import islice
from threading import RLock
from typing import Iterable


@dataclass(frozen=True)
class Frame:
    stream: str
    seq: int
    t_ms: int


@dataclass
class TelemetryBus:
    """Per-stream bounded, rate-controlled, replay-resistant synthetic bus.

    A rejected frame does not move the acceptance watermark. A batch is atomic
    by default; partial mode is opt-in and reports exactly what was applied.
    """

    max_hz: float = 100.0
    last_t: dict[str, int] = field(default_factory=dict)
    last_seq: dict[str, int] = field(default_factory=dict)
    drops: int = 0
    accepted: int = 0
    rate_limited: int = 0
    keep_history: int = 10_000
    max_batch: int = 10_000
    _per_stream_drops: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _history: list[Frame] = field(default_factory=list, repr=False)
    _rejected: dict[str, int] = field(default_factory=lambda: defaultdict(int), repr=False)
    _lock: RLock = field(default_factory=RLock, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if isinstance(self.max_hz, bool) or not isinstance(self.max_hz, (int, float)) or not math.isfinite(self.max_hz) or self.max_hz <= 0:
            raise ValueError("max_hz must be finite and > 0")
        if isinstance(self.keep_history, bool) or not isinstance(self.keep_history, int) or self.keep_history < 0:
            raise ValueError("keep_history must be a nonnegative integer")
        if isinstance(self.max_batch, bool) or not isinstance(self.max_batch, int) or not (1 <= self.max_batch <= 1_000_000):
            raise ValueError("max_batch must be an integer in [1, 1000000]")

    def _reject(self, reason: str, **details: object) -> dict:
        self._rejected[reason] += 1
        if reason == "rate_limit":
            self.rate_limited += 1
        return {"ok": False, "reason": reason, **details}

    def _ingest_locked(self, f: Frame) -> dict:
        if (not isinstance(f, Frame) or not isinstance(f.stream, str) or not f.stream.strip()
                or not isinstance(f.seq, int) or isinstance(f.seq, bool) or f.seq < 0
                or not isinstance(f.t_ms, int) or isinstance(f.t_ms, bool) or f.t_ms < 0):
            return self._reject("invalid_frame")

        prev_s = self.last_seq.get(f.stream)
        if prev_s is not None and f.seq <= prev_s:
            return self._reject("replay_or_reorder", stream=f.stream, seq=f.seq, last_seq=prev_s)
        prev_t = self.last_t.get(f.stream)
        if prev_t is not None and f.t_ms < prev_t:
            return self._reject("timestamp_reorder", stream=f.stream, t_ms=f.t_ms, last_t_ms=prev_t)

        min_dt = 1000.0 / self.max_hz
        if prev_t is not None and (f.t_ms - prev_t) < min_dt - 1e-9:
            return self._reject("rate_limit", min_dt_ms=min_dt, stream=f.stream)

        gap = 0 if prev_s is None else f.seq - prev_s - 1
        if gap:
            self.drops += gap
            self._per_stream_drops[f.stream] += gap
        self.last_t[f.stream] = f.t_ms
        self.last_seq[f.stream] = f.seq
        self.accepted += 1
        if self.keep_history:
            self._history.append(f)
            if len(self._history) > self.keep_history:
                del self._history[:-self.keep_history]
        return {
            "ok": True, "accepted": self.accepted, "drops": self.drops,
            "gap": gap, "stream": f.stream,
        }

    def ingest(self, f: Frame) -> dict:
        with self._lock:
            return self._ingest_locked(f)

    def _snapshot_locked(self) -> tuple:
        return (
            self.last_t.copy(), self.last_seq.copy(), self.drops, self.accepted,
            self.rate_limited, dict(self._per_stream_drops), self._history.copy(),
            dict(self._rejected),
        )

    def _restore_locked(self, snapshot: tuple) -> None:
        (self.last_t, self.last_seq, self.drops, self.accepted,
         self.rate_limited, stream_drops, self._history, rejected) = snapshot
        self._per_stream_drops = defaultdict(int, stream_drops)
        self._rejected = defaultdict(int, rejected)

    def ingest_batch(self, frames: Iterable[Frame], *, atomic: bool = True) -> dict:
        """Ingest a bounded batch with exact committed-versus-rejected evidence.

        Atomic mode stages all changes under one lock and restores the previous
        state if any frame fails. An oversized or uniterable batch raises before
        mutation; partial mode explicitly retains successful frames.
        """
        if not isinstance(atomic, bool):
            raise ValueError("atomic must be a boolean")
        materialized = list(islice(iter(frames), self.max_batch + 1))
        if len(materialized) > self.max_batch:
            raise ValueError("batch exceeds max_batch; no frames were applied")
        with self._lock:
            snapshot = self._snapshot_locked() if atomic else None
            results = []
            for index, frame in enumerate(materialized):
                outcome = self._ingest_locked(frame)
                results.append(outcome)
                if atomic and not outcome["ok"]:
                    self._restore_locked(snapshot)
                    return {
                        "ok": False, "committed": False, "atomic": True,
                        "rejected_index": index, "processed_count": len(results),
                        "accepted_count": 0, "results": results,
                    }
            successes = sum(r["ok"] for r in results)
            return {
                "ok": successes == len(results), "committed": bool(successes) or not materialized,
                "atomic": atomic, "rejected_index": None,
                "processed_count": len(results), "accepted_count": successes,
                "results": results,
            }

    def export_protobuf_batch(self, *, source: str = "bus") -> bytes:
        """Encode a consistent accepted-history snapshot as Protobuf."""
        from proto_codec import encode_batch
        with self._lock:
            history = self._history.copy()
        return encode_batch(history, source=source)

    def condensation_report(self, *, source: str = "bus") -> dict:
        from proto_codec import measure_condensation
        with self._lock:
            history = self._history.copy()
        return measure_condensation(history, source=source)

    def stats(self) -> dict:
        with self._lock:
            return {
                "accepted": self.accepted, "drops": self.drops,
                "rate_limited": self.rate_limited,
                "streams": len(self.last_seq), "history": len(self._history),
                "per_stream_drops": dict(self._per_stream_drops),
                "rejected_by_reason": dict(self._rejected),
            }


if __name__ == "__main__":
    bus = TelemetryBus(max_hz=10)
    print(bus.ingest_batch([Frame("imu", 1, 0), Frame("imu", 2, 50)]))
    print(bus.stats())
