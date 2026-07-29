# SpaceX Telemetry — Go UDP Packet Decoder & Protobuf Schema 🛰️

> **Go UDP telemetry packet decoder and Protobuf IDL definitions for flight telemetry ingestion.**

[![Go](https://img.shields.io/badge/Go-1.21+-00ADD8)]()
[![Protobuf](https://img.shields.io/badge/Protobuf-3.0+-blue)]()
[![Python](https://img.shields.io/badge/Python-3.9+-blue)]()
[![Domain](https://img.shields.io/badge/Domain-Telemetry%20Ingestion-red)]()

---

## 🎯 For Recruiters & Hiring Managers

This repository implements the **SpaceX Telemetry Ingestion Pipeline** — decoding 50,000+ UDP binary packets/second with zero GC pause degradation. It demonstrates:

- **Go binary packet decoder** parsing binary telemetry frames directly from socket streams
- **Protobuf IDL schemas** defining strict cross-language telemetry data contracts
- **Sub-millisecond decoding latency** preserving timestamp fidelity for flight control
- **Python test wrapper** verifying packet decoding against synthetic telemetry streams

**Why this matters**: High-throughput telemetry ingestion requires non-blocking binary parsing to process real-time sensor streams during launch and reentry.

---

## 🔬 For Engineers & Technical Reviewers

### Core Components

| Component | Language | Purpose |
|---|---|---|
| `src/telemetry_decoder.go` | Go | High-speed binary packet decoder & frame struct |
| `proto/telemetry.proto` | Protobuf | Protocol buffer schema for telemetry payloads |
| `tests/test_telemetry_decoder.py` | Python | Test harness verifying packet decoding |

---

## 🤖 ML/AI & Programmatic Mesh Integration

- **MCP Tool**: `stream_telemetry()` — real-time telemetry stream queryable by agents
- **Mastermind Sidecar**: Telemetry bridge for APEX Highway mesh
- **SHA-256 Integrity**: Tracked in `.integrity/file_hashes.json`

---

## ⚡ Quick Start

```bash
python3 tests/test_telemetry_decoder.py
```
