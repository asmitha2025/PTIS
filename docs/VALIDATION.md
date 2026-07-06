# Validation

This project validates software behavior and supporting real-data evidence. It does not yet validate field deployment impact.

## Reproducible Checks

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```

The verification script runs:

- `29` unit tests.
- `6` published scenarios.
- A deterministic `240`-vehicle batch stress test.
- A synthetic `8,000`-vehicle extreme stress test.
- A public OSRM/OpenStreetMap routed road geometry file for map-route visualization.
- Dataset manifest checks for synthetic fixtures, official DULT reference, and BMD-45 CCTV evidence.
- BMD-45 CCTV sample validation.
- Remote aggregate replay validates no-travel checkpoint-count CSVs when present; current public evidence remains pending until a real observer CSV is supplied.
- Proof report generation.

## Current Evidence

`evidence/latest_run.json` is generated, not hand-written. It contains scenario hash, posterior state, density state, compliance result, smart-link decision, and assertion details.

`evidence/batch_report.json` verifies aggregate behavior over 240 deterministic vehicles and checks for capacity violations, overcommands, and false-positive aggregate activations.

`evidence/extreme_batch_report.json` repeats the aggregate stress path at 8,000 synthetic vehicles and 23,314 observations. It is a worst-case software stress fixture, not observed field traffic.
`data/orr_silk_board_whitefield_route_osrm.geojson` stores the OSRM/OpenStreetMap routed road geometry used by the dashboard. It contains 1,185 coordinates over 37.88 km and is a visualization/reference layer, not observed vehicle trajectories.

`evidence/cctv_bmd45_report.json` validates the local BMD-45 sample:

- `10,194` metadata rows
- `10,194` COCO images
- `106,404` COCO annotations
- `13` vehicle category entries in the downloaded validation annotation file
- `5` local 1920x1080 sample images matched against metadata and COCO records

## Evidence Boundaries

BMD-45 is real Bengaluru CCTV vehicle-detection evidence. It supports detection/counting validation, not PTIS field replay.

DULT CMP/CTTP is official planning-reference evidence. It supports corridor grounding, not event-level replay.

Synthetic scenario and batch fixtures validate software behavior. They are not field-observed traffic data.

## Not Yet Proven

The repository does not yet prove:

- 43% real-world congestion reduction,
- annual economic savings,
- live Google routing coordination,
- live FASTag or ANPR identity matching,
- safe autonomous signal operation,
- field-proven route prediction.

Those require observed checkpoint/time-series data, OD labels, calibration, and agency-controlled trials.

`evidence/remote_aggregate_replay_report.json`, when generated from `remote_aggregate_counts.csv`, checks measured aggregate flow against the capacity gate under a worst-case destination-pressure assumption. It never sets `field_proven: true`.
