#!/usr/bin/env bash
set -euo pipefail

python -m pip install --disable-pip-version-check --quiet -r requirements.txt pytest 'setuptools>=75' wheel
python -m compileall -q src tests scripts mastermind_sidecar.py
python -m pytest -q tests

rm -rf dist build *.egg-info src/*.egg-info
python -m pip wheel . --no-deps --no-build-isolation -w dist
python -m pip install --disable-pip-version-check --quiet --force-reinstall dist/*.whl
telemetry-lab-demo --compact > /tmp/telemetry-lab-demo.json
python - <<'PY'
import json
from pathlib import Path
receipt = json.loads(Path('/tmp/telemetry-lab-demo.json').read_text())
assert receipt['evidence_state'] == 'LOCAL_SYNTHETIC_TELEMETRY_CODEC_NOT_SPACEX_DATA'
assert receipt['binary_frame']['decoded_frames'] == 3
assert receipt['binary_frame']['gap_count'] == 1
assert receipt['integrity_rejection']['corrupt_frame_crc_errors'] == 1
assert receipt['threshold_controller']['latest_severity'] == 'WARNING'
assert receipt['protobuf_round_trip']['stream'] == 'local-demo'
assert receipt['external_actions_executed'] == 0
assert len(receipt['digest']) == 64
PY
python scripts/operate.py

gofmt -w src/telemetry_decoder.go src/telemetry_decoder_test.go
git diff --exit-code -- src/telemetry_decoder.go src/telemetry_decoder_test.go
go vet ./...
go test ./...

python scripts/verify_public_surface.py
python - <<'PY'
import json
from pathlib import Path
caps = json.loads(Path('machine/crystallization/capability-manifest.json').read_text())
gaps = json.loads(Path('machine/crystallization/gap-matrix.json').read_text())
assert caps['capabilities']
assert all(item['state'] == 'WORKING' for item in caps['capabilities'])
assert gaps['gaps'] == []
PY
