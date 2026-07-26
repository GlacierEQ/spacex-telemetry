# Wire format — real protobuf condensation

## Why here

High-rate telemetry and helix handoffs are **volume problems**. JSON is fine for demos; protobuf is for **dense binary** that still round-trips typed fields.

## Schemas (source of truth)

- `protos/telemetry.proto` — `TelemetryFrame`, `TelemetryBatch`
- `protos/helix_envelope.proto` — `HelixEnvelope` (piston handoffs)

## Generate

```bash
bash scripts/gen_proto.sh
# requires: pip install protobuf grpcio-tools
```

## Use

```python
from telemetry_bus import Frame, TelemetryBus
from proto_codec import measure_condensation, encode_helix_envelope

bus = TelemetryBus(max_hz=1e6)
for i in range(1, 501):
    bus.ingest(Frame("imu", i, i))
blob = bus.export_protobuf_batch()   # bytes
print(bus.condensation_report())     # must show wins=True vs JSON
```

## Measured (unit tests)

On 100–200 frame loads, protobuf is **~60–70% smaller** than compact JSON in practice. Tests **fail** if protobuf does not win.

## Not theater

- Real `.proto` → generated `*_pb2.py` → `SerializeToString` / `ParseFromString`
- Bus history → batch export on the real ingest path
- Helix envelopes for cross-piston handoffs without chatty JSON bodies
