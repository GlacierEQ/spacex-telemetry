import math
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from telemetry_bus import Frame, TelemetryBus


@pytest.mark.parametrize('rate', [0, -1, float('nan'), math.inf, True])
def test_rate_validation(rate):
    with pytest.raises(ValueError):
        TelemetryBus(max_hz=rate)


@pytest.mark.parametrize('frame', [Frame('', 1, 0), Frame('s', True, 0), Frame('s', 1.5, 0), Frame('s', 1, -1), 'invalid'])
def test_no_invalid_watermarks(frame):
    b = TelemetryBus()
    assert b.ingest(frame)['reason'] == 'invalid_frame'
    assert b.last_seq == {} and b.accepted == 0


def test_bounded_batch_and_history():
    b = TelemetryBus(max_hz=1000, keep_history=2, max_batch=2)
    with pytest.raises(ValueError):
        b.ingest_batch([Frame('s', i, i * 2) for i in range(1, 4)])
    assert b.accepted == 0
    for i in range(1, 5):
        assert b.ingest(Frame('s', i, i * 2))['ok']
    assert [f.seq for f in b._history] == [3, 4]


def test_parallel_stream_isolation():
    b = TelemetryBus(max_hz=1000)
    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(b.ingest, [Frame(str(i), 1, 0) for i in range(200)]))
    assert all(x['ok'] for x in results)
    assert b.accepted == 200 and len(b.last_seq) == 200
