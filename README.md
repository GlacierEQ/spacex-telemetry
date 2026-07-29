# spacex-telemetry

<!-- README-MESH:BEGIN -->
## Three-audience project map

This section is generated from the versioned [README Mesh Protobuf contract](https://github.com/GlacierEQ/job-app-helix/blob/main/proto/readme_mesh.proto). Human explanation and machine-readable topology describe the same evidence-bound system.

### For recruiters and non-specialists

**What this project accomplishes.** A telemetry frame bus that rate-limits streams, detects gaps and replays, and exports accepted history through Protobuf.

- It turns telemetry ingestion into a concrete, reviewable software capability.
- The project is small enough to understand quickly and structured enough to connect into a larger system.
- Claims link to source or tests instead of resume language alone.

**Evidence**
- [Telemetry bus](https://github.com/GlacierEQ/spacex-telemetry/blob/main/src/telemetry_bus.py) — Implements per-stream ordering, rate limits, drop accounting, and Protobuf export.

### For senior engineers and domain experts

**Engineering depth, innovation, and evolution.** The design makes transport health measurable at ingestion time and retains a compact wire path instead of treating serialization as an afterthought. It evolved from frame accounting into real Protobuf batch export and measured JSON-versus-Protobuf condensation.

- Primary engineering capabilities: telemetry ingestion, gap detection, rate limiting, Protobuf serialization.
- The repository owns an explicit mesh responsibility rather than pretending to be an entire platform.
- Constraints and handoffs are visible through source structure and executable tests.

**Evidence**
- [Telemetry bus](https://github.com/GlacierEQ/spacex-telemetry/blob/main/src/telemetry_bus.py) — Implements per-stream ordering, rate limits, drop accounting, and Protobuf export.
- [Protobuf codec](https://github.com/GlacierEQ/spacex-telemetry/blob/main/src/proto_codec.py) — Encodes telemetry history into a real Protocol Buffers batch.
- [Tests](https://github.com/GlacierEQ/spacex-telemetry/blob/main/tests/test_telemetry_bus.py) — Exercises telemetry behavior and accounting.

### For AI systems and toolchains

**Machine contract and mesh role.** This repository is a typed node in the GlacierEQ/job-app-helix README Mesh and uses the glaciereq.readme.v1 Protobuf contract.

- Canonical repository identity: GlacierEQ/spacex-telemetry.
- Default branch: main.
- Typed edges describe composition; evidence URLs remain stable machine inputs.

**Evidence**
- [Protobuf codec](https://github.com/GlacierEQ/spacex-telemetry/blob/main/src/proto_codec.py) — Encodes telemetry history into a real Protocol Buffers batch.
- [Tests](https://github.com/GlacierEQ/spacex-telemetry/blob/main/tests/test_telemetry_bus.py) — Exercises telemetry behavior and accounting.

### Repository mesh

| Relationship | Connected repository | Combined value |
|---|---|---|
| receives: orchestrates | [GlacierEQ/job-app-helix](https://github.com/GlacierEQ/job-app-helix#readme) | Supplies ordered telemetry evidence to the campaign. |
| is governed by | [GlacierEQ/AKOS](https://github.com/GlacierEQ/AKOS#readme) | AKOS supplies the shared evidence, authority, provenance, and public-boundary contract. |
| provides capability to | [GlacierEQ/spacex-autonomy](https://github.com/GlacierEQ/spacex-autonomy#readme) | Autonomy consumes bounded, ordered vehicle-state evidence rather than raw unchecked events. |
| provides capability to | [GlacierEQ/spacex-mission-control](https://github.com/GlacierEQ/spacex-mission-control#readme) | Mission control receives ordered, rate-limited telemetry with explicit loss accounting. |

### Machine-readable contract

- Protobuf package: `glaciereq.readme.v1`
- Mesh schema version: `1.0.0`
- Canonical mesh: [`manifests/readme_mesh.json`](https://github.com/GlacierEQ/job-app-helix/blob/main/manifests/readme_mesh.json)
- Binary/ProtoJSON build: `python -m job_app_helix.readme_mesh_cli build`
- Repository identity: `GlacierEQ/spacex-telemetry`

```protobuf
repository: "GlacierEQ/spacex-telemetry"
display_name: "SpaceX Telemetry"
one_line_purpose: "A telemetry frame bus that rate-limits streams, detects gaps and replays, and exports accepted history through Protobuf."
```
<!-- README-MESH:END -->

**Portfolio** — telemetry ingest with rate limit + sequence drop detection.

---

## Fleet ops (transparent)

This repo may include `.integrity/` (SHA-256 integrity) and/or a health sidecar.
These are **documented fleet operations**, not covert implants. See [SECURITY_AND_FLEET_OPS.md](SECURITY_AND_FLEET_OPS.md).

## Helix strand

See [HELIX_STRAND.md](HELIX_STRAND.md) — piston/spiral role in the portfolio double helix.
