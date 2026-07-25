# Issue Contract — `spacex-telemetry`

## Pain
High-rate streams overwhelm consumers; sequence gaps hide dropped frames.

## Claim
TelemetryBus enforces max_hz and detects sequence gaps/replays.

## Proof
```bash
python3 job-app/helix/proofs/proof_telemetry.py
```

## Done when
Proof exits 0. Architecture (strand/integrity/helix) is **not** a substitute for this proof.

## Anti-claim
Not flight-certified avionics.
