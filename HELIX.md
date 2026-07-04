# HELIX Architecture — spacex-telemetry

## Double Helix Pattern

**Alpha (What)** — Pure physics models, stateless computation
- __init__,telemetry_decoder

**Omega (How)** — Controllers, orchestration, stateful management  
- information_fingerprint,__init__,telemetry_controller

## Design Principles

- Zero external dependencies (stdlib only)
- Stateless alpha, stateful omega
- SHA-256 file integrity verification
- Shadow watchdog daemon monitoring
- Mastermind sidecar coordination

## Data Flow

```
Alpha Models → Omega Controllers → Mastermind Sidecar → Shadow Infrastructure
```
