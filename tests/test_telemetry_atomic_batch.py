import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from telemetry_bus import Frame, TelemetryBus


def test_atomic_rollback():
    b = TelemetryBus(max_hz=1000)
    b.ingest(Frame('a', 5, 0))
    before = b.stats()
    r = b.ingest_batch([Frame('a', 6, 5), Frame('a', 6, 6)])
    assert not r['ok'] and not r['committed']
    assert r['rejected_index'] == 1 and r['accepted_count'] == 0
    assert b.stats() == before


def test_partial_real_effects():
    b = TelemetryBus(max_hz=1000)
    r = b.ingest_batch([Frame('a', 1, 0), Frame('a', 1, 2), Frame('a', 4, 5)], atomic=False)
    assert not r['ok'] and r['committed']
    assert r['accepted_count'] == 2
    assert b.stats()['drops'] == 2


def test_replay_precedes_rate_limit():
    b = TelemetryBus(max_hz=1)
    b.ingest(Frame('a', 5, 1000))
    assert b.ingest(Frame('a', 5, 1001))['reason'] == 'replay_or_reorder'
    assert b.ingest(Frame('a', 6, 999))['reason'] == 'timestamp_reorder'
    assert b.rate_limited == 0
