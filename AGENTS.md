# AGENTS — spacex-telemetry

## Agent Roles

### Alpha Agent — Decoder
- Owns frame parsing, CRC validation, sequence tracking
- Stateless: feed bytes, get readings
- Interface: `TelemetryDecoder.feed(raw) -> list[TelemetryReading]`

### Omega Agent — Controller
- Owns alerting, health monitoring, time-series storage
- Stateful: maintains rolling windows and ring buffer
- Interface: `TelemetryController.feed(raw) -> int`

### Shadow Agent — Watchdog
- Owns file integrity verification
- Runs independently, reports violations
- Interface: `watchdog_daemon.run_check() -> dict`

## Communication

- Alpha → Omega: via callback registration (`decoder.register_callback`)
- Omega → Shadow: via file integrity checks
- No cross-imports between Alpha and Omega beyond data types
