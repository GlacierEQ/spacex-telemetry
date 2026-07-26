"""Real protobuf codecs for telemetry batches and helix envelopes.

Measures condensation vs JSON. Not decorative — wire bytes for high-rate paths.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, Sequence

# Generated modules (local)
try:
    from glaciereq_pb.telemetry_pb2 import TelemetryBatch, TelemetryFrame
    from glaciereq_pb.helix_envelope_pb2 import HelixEnvelope
except ImportError:  # package layout
    from glaciereq_pb import helix_envelope_pb2, telemetry_pb2

    TelemetryBatch = telemetry_pb2.TelemetryBatch
    TelemetryFrame = telemetry_pb2.TelemetryFrame
    HelixEnvelope = helix_envelope_pb2.HelixEnvelope


def _frame_to_pb(stream: str, seq: int, t_ms: int, payload: bytes = b"", metrics: dict | None = None) -> TelemetryFrame:
    msg = TelemetryFrame()
    msg.stream = stream
    msg.seq = int(seq)
    msg.t_ms = int(t_ms)
    if payload:
        msg.payload = payload
    if metrics:
        for k, v in metrics.items():
            msg.metrics[str(k)] = float(v)
    return msg


def encode_frame(stream: str, seq: int, t_ms: int, payload: bytes = b"", metrics: dict | None = None) -> bytes:
    return _frame_to_pb(stream, seq, t_ms, payload, metrics).SerializeToString()


def decode_frame(data: bytes) -> dict[str, Any]:
    msg = TelemetryFrame()
    msg.ParseFromString(data)
    return {
        "stream": msg.stream,
        "seq": msg.seq,
        "t_ms": msg.t_ms,
        "payload": bytes(msg.payload),
        "metrics": dict(msg.metrics),
    }


def encode_batch(
    frames: Sequence[dict[str, Any] | Any],
    *,
    source: str = "bus",
    produced_at_ms: int | None = None,
) -> bytes:
    batch = TelemetryBatch()
    batch.source = source
    batch.produced_at_ms = int(
        produced_at_ms if produced_at_ms is not None else time.time() * 1000
    )
    for f in frames:
        if is_dataclass(f) and not isinstance(f, type):
            d = asdict(f)
        elif isinstance(f, dict):
            d = f
        else:
            d = {"stream": getattr(f, "stream"), "seq": getattr(f, "seq"), "t_ms": getattr(f, "t_ms")}
        batch.frames.append(
            _frame_to_pb(
                d["stream"],
                d["seq"],
                d["t_ms"],
                d.get("payload") or b"",
                d.get("metrics"),
            )
        )
    return batch.SerializeToString()


def decode_batch(data: bytes) -> dict[str, Any]:
    batch = TelemetryBatch()
    batch.ParseFromString(data)
    return {
        "source": batch.source,
        "produced_at_ms": batch.produced_at_ms,
        "frames": [
            {
                "stream": f.stream,
                "seq": f.seq,
                "t_ms": f.t_ms,
                "payload": bytes(f.payload),
                "metrics": dict(f.metrics),
            }
            for f in batch.frames
        ],
    }


def encode_helix_envelope(
    *,
    pair_id: str,
    piston: str,
    spiral: str,
    status: str,
    numbers: dict[str, float] | None = None,
    tags: dict[str, str] | None = None,
    json_fallback: dict | None = None,
    ts_ms: int | None = None,
) -> bytes:
    msg = HelixEnvelope()
    msg.pair_id = pair_id
    msg.piston = piston
    msg.spiral = spiral
    msg.status = status
    msg.ts_ms = int(ts_ms if ts_ms is not None else time.time() * 1000)
    if numbers:
        for k, v in numbers.items():
            msg.numbers[str(k)] = float(v)
    if tags:
        for k, v in tags.items():
            msg.tags[str(k)] = str(v)
    if json_fallback is not None:
        msg.json_fallback = json.dumps(json_fallback, separators=(",", ":")).encode()
    return msg.SerializeToString()


def decode_helix_envelope(data: bytes) -> dict[str, Any]:
    msg = HelixEnvelope()
    msg.ParseFromString(data)
    out: dict[str, Any] = {
        "pair_id": msg.pair_id,
        "piston": msg.piston,
        "spiral": msg.spiral,
        "status": msg.status,
        "ts_ms": msg.ts_ms,
        "numbers": dict(msg.numbers),
        "tags": dict(msg.tags),
    }
    if msg.json_fallback:
        out["json_fallback"] = json.loads(msg.json_fallback.decode())
    return out


def measure_condensation(
    frames: Sequence[dict[str, Any] | Any],
    *,
    source: str = "bus",
) -> dict[str, Any]:
    """Compare protobuf batch size vs compact JSON — must show real savings on realistic loads."""
    # JSON baseline (compact)
    serializable = []
    for f in frames:
        if is_dataclass(f) and not isinstance(f, type):
            d = asdict(f)
        elif isinstance(f, dict):
            d = dict(f)
        else:
            d = {"stream": f.stream, "seq": f.seq, "t_ms": f.t_ms}
        # drop empty payload for fair json
        if not d.get("payload"):
            d.pop("payload", None)
        if not d.get("metrics"):
            d.pop("metrics", None)
        serializable.append(d)
    json_bytes = json.dumps(
        {"source": source, "frames": serializable},
        separators=(",", ":"),
    ).encode()
    pb_bytes = encode_batch(frames, source=source)
    jn, pn = len(json_bytes), len(pb_bytes)
    ratio = pn / jn if jn else 1.0
    return {
        "json_bytes": jn,
        "protobuf_bytes": pn,
        "ratio_pb_over_json": round(ratio, 4),
        "savings_pct": round(100.0 * (1.0 - ratio), 2) if jn else 0.0,
        "wins": pn < jn,
        "n_frames": len(frames),
    }
