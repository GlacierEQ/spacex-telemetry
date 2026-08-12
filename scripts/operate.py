#!/usr/bin/env python3
"""Execute the repository's canonical synthetic telemetry product surface."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from telemetry_lab_cli import EVIDENCE_STATE, build_demo_receipt  # noqa: E402


def main() -> int:
    receipt = build_demo_receipt()
    print(json.dumps(receipt, indent=2, sort_keys=True))
    valid = (
        receipt["evidence_state"] == EVIDENCE_STATE
        and receipt["binary_frame"]["decoded_frames"] == 3
        and receipt["binary_frame"]["gap_count"] == 1
        and receipt["binary_frame"]["dropped_frames"] == 1
        and receipt["integrity_rejection"]["corrupt_frame_crc_errors"] == 1
        and receipt["integrity_rejection"]["decoded_frames"] == 0
        and receipt["threshold_controller"]["alert_count"] == 1
        and receipt["threshold_controller"]["latest_severity"] == "WARNING"
        and receipt["protobuf_round_trip"]["stream"] == "local-demo"
        and receipt["external_inputs_consumed"] == 0
        and receipt["external_actions_executed"] == 0
        and len(receipt["digest"]) == 64
    )
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
