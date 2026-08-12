from __future__ import annotations

import json
import subprocess
import sys

from telemetry_lab_cli import EVIDENCE_STATE, build_demo_receipt


def test_demo_receipt_exercises_material_telemetry_mechanisms() -> None:
    receipt = build_demo_receipt()
    assert receipt["evidence_state"] == EVIDENCE_STATE
    assert receipt["binary_frame"]["decoded_frames"] == 3
    assert receipt["binary_frame"]["gap_count"] == 1
    assert receipt["binary_frame"]["dropped_frames"] == 1
    assert receipt["integrity_rejection"] == {
        "corrupt_frame_crc_errors": 1,
        "decoded_frames": 0,
    }
    assert receipt["threshold_controller"]["alert_count"] == 1
    assert receipt["threshold_controller"]["latest_severity"] == "WARNING"
    assert receipt["protobuf_round_trip"]["payload"] == "demo"
    assert receipt["external_inputs_consumed"] == 0
    assert receipt["external_actions_executed"] == 0
    assert len(receipt["digest"]) == 64


def test_operate_script_is_direct_and_machine_readable() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/operate.py"],
        check=True,
        capture_output=True,
        text=True,
    )
    receipt = json.loads(result.stdout)
    assert receipt["evidence_state"] == EVIDENCE_STATE
    assert receipt["protobuf_round_trip"]["seq"] == 7
