# SpaceX Telemetry Pipeline

Real-time telemetry frame decoder and pipeline controller for Falcon 9 / Starship downlinks.

## Architecture

**Double Helix (Alpha + Omega)**

- **Alpha** (`src/alpha/telemetry_decoder.py`): Pure decoding — CCSDS-like frame parsing, CRC-16 validation, sequence gap detection. Stateless sensor extraction.
- **Omega** (`src/omega/telemetry_controller.py`): Pipeline routing — threshold alerts, rolling-window sensor health, time-series ring buffer. Stateful orchestration.

## Key Features

- Zero external dependencies (stdlib only)
- CCSDS-compatible frame sync (`0x1ACF`)
- CRC-16 CCITT error detection
- Sequence counter gap detection for dropped frames
- Rolling-window sensor health (mean, variance, rate-of-change)
- Configurable threshold alerts with consecutive breach detection
- Ring buffer time-series query
- Shadow watchdog with SHA-256 file integrity

## Usage

```python
from src.alpha.telemetry_decoder import TelemetryDecoder, SensorType, encode_frame
from src.omega.telemetry_controller import TelemetryController, Threshold

controller = TelemetryController()
controller.add_threshold(Threshold(SensorType.TEMPERATURE, min_val=200, max_val=400))

frame = encode_frame(src=1, dst=2, seq=0, sensors=[
    (1, SensorType.TEMPERATURE, 100, 933.15),
])
controller.feed(frame)
print(controller.pipeline_stats)
```

## Tests

```bash
python tests/test_telemetry.py
```

## Stealth Infrastructure

`.shadow/` contains watchdog daemon and SHA-256 integrity verification for all source files.
