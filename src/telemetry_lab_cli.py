"""Deterministic executable surface for the synthetic telemetry laboratory."""
from __future__ import annotations

import argparse
import hashlib
import json
from typing import Any

from alpha.telemetry_decoder import SensorType, TelemetryDecoder, encode_frame as encode_binary_frame
from omega.telemetry_controller import TelemetryController, Threshold
from proto_codec import decode_frame as decode_proto_frame
from proto_codec import encode_frame as encode_proto_frame

EVIDENCE_STATE = "LOCAL_SYNTHETIC_TELEMETRY_CODEC_NOT_SPACEX_DATA"


def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_demo_receipt() -> dict[str, Any]:
    """Exercise framing, CRC refusal, gap accounting, threshold alerts, and protobuf."""
    decoder = TelemetryDecoder(buffer_size=2048)
    controller = TelemetryController(decoder)
    controller.add_threshold(
        Threshold(
            sensor_type=SensorType.TEMPERATURE,
            min_val=250.0,
            max_val=320.0,
            consecutive_breaches=2,
        )
    )

    controller.feed(encode_binary_frame(1, 2, 1, [(7, SensorType.TEMPERATURE, 0, 300.0)]))
    controller.feed(encode_binary_frame(1, 2, 2, [(7, SensorType.TEMPERATURE, 0, 350.0)]))
    controller.feed(encode_binary_frame(1, 2, 4, [(7, SensorType.TEMPERATURE, 0, 355.0)]))

    crc_decoder = TelemetryDecoder(buffer_size=512)
    corrupt = bytearray(
        encode_binary_frame(1, 2, 9, [(3, SensorType.PRESSURE, 0, 101.5)])
    )
    corrupt[-1] ^= 0xFF
    crc_decoder.feed(bytes(corrupt))

    proto_bytes = encode_proto_frame(
        "local-demo",
        7,
        1_700_000_000_000,
        b"demo",
        {"temperature": 355.0},
    )
    proto_round_trip = decode_proto_frame(proto_bytes)

    alerts = controller.active_alerts
    health = controller.get_sensor_health(7)
    receipt: dict[str, Any] = {
        "schema": "glaciereq.synthetic-telemetry-lab.demo.v1",
        "evidence_state": EVIDENCE_STATE,
        "binary_frame": {
            "decoded_frames": decoder.stats.decoded_frames,
            "last_sequence": decoder.stats.last_sequence,
            "dropped_frames": decoder.stats.dropped_frames,
            "gap_count": decoder.stats.gap_count,
            "crc_errors": decoder.stats.crc_errors,
        },
        "integrity_rejection": {
            "corrupt_frame_crc_errors": crc_decoder.stats.crc_errors,
            "decoded_frames": crc_decoder.stats.decoded_frames,
        },
        "threshold_controller": {
            "sensor_id": 7,
            "sample_mean": None if health is None else round(health.mean, 6),
            "breach_count": None if health is None else health.breach_count,
            "alert_count": len(alerts),
            "latest_severity": None if not alerts else alerts[-1].severity,
        },
        "protobuf_round_trip": {
            "encoded_bytes": len(proto_bytes),
            "stream": proto_round_trip["stream"],
            "seq": proto_round_trip["seq"],
            "t_ms": proto_round_trip["t_ms"],
            "payload": proto_round_trip["payload"].decode("utf-8"),
            "temperature": proto_round_trip["metrics"]["temperature"],
        },
        "external_inputs_consumed": 0,
        "external_actions_executed": 0,
    }
    receipt["digest"] = _digest(receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Execute the independent synthetic telemetry codec laboratory"
    )
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args(argv)
    receipt = build_demo_receipt()
    print(json.dumps(receipt, sort_keys=True, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
