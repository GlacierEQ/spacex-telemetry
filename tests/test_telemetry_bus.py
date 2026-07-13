import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from telemetry_bus import TelemetryBus, Frame, ANSWER

def test_rate_limit():
    b = TelemetryBus(max_hz=10)
    assert b.ingest(Frame("a", 1, 0))["ok"]
    assert b.ingest(Frame("a", 2, 10))["ok"] is False

def test_drop_count():
    b = TelemetryBus(max_hz=1000)
    b.ingest(Frame("a", 1, 0))
    r = b.ingest(Frame("a", 4, 5))
    assert r["drops"]==2 and r["answer"]==ANSWER

if __name__=="__main__":
    test_rate_limit(); test_drop_count(); print("ok")
