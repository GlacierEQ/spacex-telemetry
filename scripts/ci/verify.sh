#!/usr/bin/env bash
set -euo pipefail

python -m pip install --disable-pip-version-check --quiet -r requirements.txt pytest
python -m compileall -q src tests scripts mastermind_sidecar.py
python -m pytest -q tests
python scripts/operate.py

gofmt -w src/telemetry_decoder.go src/telemetry_decoder_test.go
git diff --exit-code -- src/telemetry_decoder.go src/telemetry_decoder_test.go
go vet ./...
go test ./...

python scripts/verify_public_surface.py
