#!/usr/bin/env bash
# Regenerate Python protobuf modules from protos/*.proto
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/src/glaciereq_pb"
mkdir -p "$OUT"
python3 -m grpc_tools.protoc \
  -I "$ROOT/protos" \
  --python_out="$OUT" \
  "$ROOT/protos/telemetry.proto" \
  "$ROOT/protos/helix_envelope.proto"
printf '%s\n' '"""Generated protobuf messages for GlacierEQ telemetry/helix."""' > "$OUT/__init__.py"
echo "generated into $OUT"
