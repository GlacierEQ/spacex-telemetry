# SpaceX Telemetry — Synthetic Telemetry Codec Laboratory

> **APEX dual-plane recovery:** verified lab proof remains `LOCAL_SYNTHETIC_TELEMETRY_CODEC_NOT_SPACEX_DATA` (not SpaceX flight authority). Implemented software planes are restored as first-class capabilities under MAXIMUM_COHERENT_ADVANCE — governance routes power; it does not amputate it.

**Implemented planes:** telemetry-bus-fanout, protobuf-mesh-bridge-surface, lab-cli-operate-path, multi-language-decoder-surface

**An installable repository-local Python/Go telemetry codec and controller laboratory with CRC rejection, bounded buffering, sequence-gap accounting, threshold alerts, Protobuf round trips, and a strict Go demonstration packet codec.**

> **Independence / non-affiliation:** This is an independent GlacierEQ engineering portfolio project. It is not affiliated with, endorsed by, or based on private systems, telemetry, wire formats, mission criteria, or data from SpaceX. The repository name describes a portfolio target/domain exercise, not provenance.

**Canonical branch:** `main`  
**Evidence state:** `LOCAL_SYNTHETIC_TELEMETRY_CODEC_NOT_SPACEX_DATA`

## Working product surface

The verified software is a local telemetry laboratory, not production telemetry infrastructure:

- Python binary framing with a repository-defined sync marker, CRC-16-CCITT rejection, bounded partial-frame buffering, sequence-gap accounting, typed sensor records, and callbacks;
- Python rolling sensor health, threshold breach tracking, alert generation, and bounded in-memory history;
- real generated Protobuf frame/batch/envelope codecs for local serialization experiments;
- a strict Go 13-byte demonstration packet encoder/decoder with round-trip and invalid-input tests;
- a deterministic installed `telemetry-lab-demo` command that exercises framing, an intentional sequence gap, corrupted-CRC refusal, a local threshold alert, and a Protobuf round trip without external input or side effects.

## Install and execute

```bash
python -m pip install .
telemetry-lab-demo
python scripts/operate.py
```

Repository-native proof:

```bash
bash scripts/ci/verify.sh
```

That gate runs the complete Python suite, builds and installs the wheel, executes the installed CLI, runs the direct canonical operator, verifies Go formatting/vet/tests, enforces the public truth boundary, and requires every crystallization capability to be `WORKING` with an empty material gap matrix.

## Engineering anatomy

| Surface | Verified role | Boundary |
|---|---|---|
| `src/alpha/telemetry_decoder.py` | synthetic framed binary codec | local bytes only; no external telemetry |
| `src/omega/telemetry_controller.py` | threshold/ring-buffer controller | in-memory local state |
| `src/proto_codec.py` + `src/glaciereq_pb/` | generated Protobuf serialization | local serialization only |
| `src/telemetry_decoder.go` | deterministic 13-byte demo codec | repository-defined format, not a flight wire format |
| `src/telemetry_lab_cli.py` | installed deterministic product/demo surface | zero external inputs/actions |
| `scripts/operate.py` | direct repository operability probe | invokes real mechanisms, no reflection theater |
| `tests/` | deterministic and adversarial proof | synthetic repository-owned fixtures |
| `machine/crystallization/` | purpose/capability/gap/execution proof | no external authority |

## Evidence boundary

`LOCAL_SYNTHETIC_TELEMETRY_CODEC_NOT_SPACEX_DATA`

A green repository workflow does **not** establish:

- SpaceX employment, endorsement, affiliation, internal architecture, data access, or telemetry provenance;
- Falcon, Starship, launch, re-entry, or flight-control protocol compatibility;
- CCSDS compliance;
- live UDP/socket ingestion merely because binary decoders exist;
- 50,000+ packets/second throughput, zero-GC behavior, or sub-millisecond latency;
- operational timestamp fidelity;
- live MCP tool exposure or real-time agent telemetry queries;
- live Mastermind, APEX, AKOS, or other GlacierEQ runtime connectivity;
- production deployment, reliability, scale, safety, or mission authority.

Historical files may retain older operational/fleet language as provenance. They cannot outrank this README, the exact-head public truth gate, source behavior, or a source-bound completion receipt.

## Machine entrypoint

```yaml
schema: glaciereq.readme.v2
repository: GlacierEQ/spacex-telemetry
canonical_branch: main
purpose: >-
  Demonstrate deterministic synthetic telemetry framing, integrity rejection,
  sequence accounting, local threshold control, local Protobuf serialization,
  and a bounded Go packet codec through an installable local product surface.
status:
  state: FUNCTIONAL_CRYSTALLIZATION_CANDIDATE
  evidence_token: LOCAL_SYNTHETIC_TELEMETRY_CODEC_NOT_SPACEX_DATA
```
