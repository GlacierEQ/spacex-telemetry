from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "LOCAL_SYNTHETIC_TELEMETRY_CODEC_NOT_SPACEX_DATA"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> None:
    readme = read("README.md")
    python_codec = read("src/alpha/telemetry_decoder.py")
    go_codec = read("src/telemetry_decoder.go")
    proto = read("protos/telemetry.proto")
    capabilities = json.loads(read("machine/capabilities.json"))
    target = json.loads(read("machine/target-contract.json"))

    assert TOKEN in readme
    assert TOKEN == target["evidence_token"]
    assert "not affiliated with, endorsed by" in readme
    assert "synthetic telemetry frame codec" in python_codec.lower()
    assert "not a spacex, falcon, starship, ccsds" in python_codec.lower()
    assert "not a SpaceX, Falcon, Starship, CCSDS" in go_codec
    assert "not a SpaceX, Falcon, Starship, CCSDS" in proto
    assert "SpaceX Telemetry Ingestion Pipeline" not in readme
    assert "decoding 50,000+ UDP binary packets/second" not in readme
    assert "Sub-millisecond decoding latency" not in readme
    assert "Fully wired into APEX Highway mesh" not in readme
    assert "hyper-scaling" not in capabilities["capabilities"]
    assert target["current"]["deployed"] is False

    print(TOKEN)


if __name__ == "__main__":
    main()
