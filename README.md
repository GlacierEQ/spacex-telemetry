# SpaceX Telemetry — Synthetic Telemetry Codec Laboratory

**A repository-local Python/Go telemetry codec and controller laboratory with CRC rejection, buffering, sequence-gap accounting, threshold alerts, and a generic Protobuf interchange schema.**

> **Independence / non-affiliation:** This is an independent GlacierEQ engineering portfolio project. It is not affiliated with, endorsed by, or based on private systems, telemetry, wire formats, mission criteria, or data from SpaceX. The repository name describes a portfolio target/domain exercise, not provenance.

**Canonical branch:** `main`  
**Current evidence state:** `LOCAL_SYNTHETIC_TELEMETRY_CODEC_NOT_SPACEX_DATA`

## Recruiter view

The verified engineering value is deterministic telemetry handling—not production throughput theater.

This repository demonstrates:

- a Python binary frame codec with buffering, CRC-16-CCITT rejection, sequence-gap accounting, typed sensor records, callbacks, and bounded memory;
- a Python controller with rolling sensor health, threshold alerts, and an in-memory ring buffer;
- a Go 13-byte demonstration packet decoder/encoder that parses actual encoded float fields instead of returning decorative hard-coded values;
- a generic Protobuf schema for local serialization experiments;
- repository-native Python and Go tests that exercise the current source directly.

No benchmark result is promoted unless a benchmark is actually run, recorded, and bound to the exact source revision.

## Engineering anatomy

| Surface | Verified role | Boundary |
|---|---|---|
| `src/alpha/telemetry_decoder.py` | synthetic framed binary codec | local bytes only; no external telemetry |
| `src/omega/telemetry_controller.py` | threshold/ring-buffer controller | in-memory local state |
| `src/telemetry_decoder.go` | deterministic 13-byte demo codec | repository-defined format, not a flight wire format |
| `src/telemetry_decoder_test.go` | Go correctness proof | round trip + invalid-input behavior |
| `protos/telemetry.proto` | generic local interchange schema | no provenance or transport implied |
| `tests/` | Python behavioral proof | synthetic repository-owned fixtures |

### Python frame behavior

The Python codec owns a synthetic framed format with:

- sync marker `0x1ACF` used as a repository-local framing choice;
- CRC-16-CCITT over the payload;
- bounded input buffering;
- partial-frame buffering;
- bad-CRC rejection;
- sequence-gap accounting;
- typed sensor decoding.

Use of a familiar framing or checksum mechanism does not make the format an official or proprietary telemetry protocol.

### Go packet behavior

The Go demo format is exactly 13 bytes:

```text
0..3    uint32 sequence      big-endian
4..7    float32 altitude     IEEE-754 big-endian bits
8..11   float32 velocity     IEEE-754 big-endian bits
12      uint8 status
```

The strict decoder rejects wrong packet lengths and non-finite numeric values. The compatibility decoder preserves the original zero-value-on-invalid API.

## Native proof

```bash
python -m pip install -r requirements.txt
python -m pytest -q tests
python scripts/operate.py

gofmt -w src/telemetry_decoder.go src/telemetry_decoder_test.go
go vet ./...
go test ./...

bash scripts/ci/verify.sh
```

The Public Truth Gate runs repository-owned verification against the exact pull-request head or canonical push SHA.

## Evidence boundary

`LOCAL_SYNTHETIC_TELEMETRY_CODEC_NOT_SPACEX_DATA`

A green repository workflow does **not** establish:

- SpaceX employment, endorsement, affiliation, internal architecture, data access, or telemetry provenance;
- Falcon, Starship, launch, re-entry, or flight-control protocol compatibility;
- CCSDS compliance;
- live UDP/socket ingestion merely because binary decoders exist;
- 50,000+ packets/second throughput;
- zero-GC-pause behavior;
- sub-millisecond latency;
- operational timestamp fidelity;
- live MCP tool exposure or real-time agent telemetry queries;
- live Mastermind, APEX, AKOS, or other GlacierEQ runtime connectivity;
- production deployment, reliability, scale, safety, or mission authority.

## Historical / aspirational surfaces

Older repository notes may use operational, fleet, mesh, or company-specific language. Those files are preserved as history/topology unless a current exact-head native proof explicitly promotes the claim. The README and current public truth gate define the public evidence boundary.

## Machine entrypoint

```yaml
schema: glaciereq.readme.v1
repository: GlacierEQ/spacex-telemetry
canonical_branch: main
purpose: >-
  Demonstrate deterministic synthetic telemetry framing, integrity rejection,
  sequence accounting, local threshold control, and a bounded Go packet codec.
status:
  state: LOCAL_OPERABLE
  evidence_level: TEST
  evidence_token: LOCAL_SYNTHETIC_TELEMETRY_CODEC_NOT_SPACEX_DATA
verified_surfaces:
  - Python synthetic frame encode/decode
  - CRC rejection and partial-frame buffering
  - sequence-gap accounting
  - threshold alerts and local ring-buffer queries
  - Go binary encode/decode round trip
  - generic Protobuf schema source
blocked_scope:
  - external or proprietary telemetry
  - company affiliation
  - production throughput or latency
  - flight-control compatibility or authority
  - live provider, MCP, or mesh integration
```
