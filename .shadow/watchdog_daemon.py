"""Shadow watchdog — monitors telemetry decoder health and file integrity."""

import hashlib
import json
import os
import time
from pathlib import Path

SHADOW_DIR = Path(__file__).parent
PROJECT_ROOT = SHADOW_DIR.parent
MEMORY_FILE = SHADOW_DIR / "shadow_memory.json"


def compute_file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_memory() -> dict:
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE) as f:
            return json.load(f)
    return {"checksums": {}, "last_check": 0, "violations": 0}


def save_memory(mem: dict):
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f, indent=2)


def run_check():
    mem = load_memory()
    violations = 0
    tracked = [PROJECT_ROOT / "src" / "alpha" / "telemetry_decoder.py",
               PROJECT_ROOT / "src" / "omega" / "telemetry_controller.py"]

    for path in tracked:
        if not path.exists():
            violations += 1
            continue
        current_hash = compute_file_hash(path)
        key = str(path.relative_to(PROJECT_ROOT))
        if key in mem["checksums"] and mem["checksums"][key] != current_hash:
            violations += 1
        mem["checksums"][key] = current_hash

    mem["violations"] += violations
    mem["last_check"] = time.time()
    save_memory(mem)

    return {
        "status": "PASS" if violations == 0 else "VIOLATION",
        "files_checked": len(tracked),
        "violations": violations,
        "total_historical_violations": mem["violations"],
    }


if __name__ == "__main__":
    result = run_check()
    print(json.dumps(result, indent=2))
