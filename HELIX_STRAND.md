# HELIX strand — `spacex-telemetry`

## Law

- **Piston:** local loop: in → work → out
- **Spiral:** pistons in series; every output is the next input
- **Double helix:** two separate spiral engines pointed at the same star
- **Mutual acceleration:** Alpha truth feeds Omega ops; Omega evidence feeds Alpha refinement

## This leaf

| Pair | Spiral | Role | Star |
|------|--------|------|------|
| `flight` | **bridge** | Rate/gap bus — truth of what was heard | Flight awareness — know the orbit, command the consoles, hear the bus |
| `spacex_propulsion` | **bridge** | Shared bus between prop and launch | Propulsion awareness — chamber health feeds pad ops |
| `launch_campaign` | **bridge** | Shared bus across campaign stars | Launch campaign go/no-go — multi-star meta-spiral (flight + prop + ground) |

### How this accelerates its twin

- **flight:** bridge medium (telemetry/bus) between spirals.
- **spacex_propulsion:** bridge medium (telemetry/bus) between spirals.
- **launch_campaign:** bridge medium (telemetry/bus) between spirals.

## Runtime

```bash
python3 ~/GlacierEQ_Swarm/automations/jobapp_helix_spiral.py run --all
python3 ~/GlacierEQ_Swarm/automations/jobapp_solidify_flipper.py
```

Portfolio doctrine: `~/job-app/HELIX.md`
