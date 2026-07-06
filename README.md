# PTIS v2.0

Predictive Traffic Intelligence System, rebuilt as a real runnable project instead of a concept-only document.

This repository proves the local decision engine against reproducible scenario data, grounds the Bengaluru corridor with official DULT/CMP planning references, and now audits a real public Bengaluru CCTV vehicle-detection dataset sample from BMD-45. It does not claim live FASTag, BTP, Google, field-sensor, or field-impact integration until those feeds and permissions are actually connected.

## What Works Now

- Bayesian destination inference from junction no-turn observations.
- Mid-route vehicle handling through reachable-destination priors.
- LWR two-wheeler density propagation with explicit units.
- PID-style compliance command scaling.
- Capacity-safe smart-link activation that cannot command more expected diversion than available receiving capacity.
- Reproducible scenario evidence in `evidence/latest_run.json`.
- Deterministic 240-vehicle batch stress evidence in `evidence/batch_report.json`.
- Synthetic 8,000-vehicle extreme stress evidence in `evidence/extreme_batch_report.json`.
- Official DULT/CMP planning-reference extract in `data/official_reference_bengaluru_cmp_2020.json`.
- OSRM/OpenStreetMap routed road geometry in `data/orr_silk_board_whitefield_route_osrm.geojson`.
- Real public BMD-45 CCTV validation evidence in `evidence/cctv_bmd45_report.json`.
- Field replay pipeline with strict CSV validation in `backend/ptis_core/field_replay.py`.
- Remote aggregate-count validation/replay lane in `backend/ptis_core/remote_aggregate.py` for no-travel measured-load checks.
- Static operations dashboard backed by the same evidence JSON/API.

## Verified Evidence

Run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```

Current proof suite:

- Unit tests: `29/29` passed
- Scenario suite: `6/6` passed
- Batch stress test: `240` vehicles, `689` observations, `0` capacity violations, `0` overcommands, `0` false-positive aggregate activations
- Extreme stress test: `8,000` vehicles, `23,314` observations, `0` capacity violations, `0` overcommands, `0` false-positive aggregate activations
- BMD-45 CCTV evidence: `10,194` metadata rows, `10,194` COCO images, `106,404` COCO annotations, `5` local 1080p sample images audited
- Official planning reference: DULT CMP Bengaluru 2020 + CTTP executive summary, with source pages and SHA-256 checksums
- Real route geometry: OSRM/OpenStreetMap routed road line, `1,185` coordinates, `37.88` km, visualization only, not live traffic
- Field replay gate: implemented; waiting for real observation, capacity and ground-truth CSVs

The generated proof report is `evidence/PROOF_REPORT.md`. For external review, use `docs/PUBLIC_EVIDENCE_BRIEF.md` and `docs/LINKEDIN_REVIEW_PACKAGE.md`.

## Real CCTV Evidence Boundary

The local BMD-45 sample is useful real-world evidence for a vehicle detection/counting layer. It proves the project can audit public Bengaluru CCTV imagery and COCO annotations with provenance and checksums.

It does not prove PTIS route prediction or field impact because BMD-45 is not anonymized multi-checkpoint vehicle trajectory data and does not include OD ground-truth labels.

## Field Replay Gate

The project includes headers-only CSV templates in `data/field_observed/templates/` plus a real-data runbook in `docs/FIELD_SURVEY_RUNBOOK.md`.

If the project owner cannot physically visit Bengaluru, use `docs/REMOTE_VALIDATION_PATH.md` and `docs/REMOTE_OBSERVER_PACKET.md`. This gives the project a defensible no-travel path: keep the current public claim at software validation plus public evidence, then collect remote aggregate counts through a trusted observer. Remote aggregate counts can support a measured-load safety replay, but they still do not unlock a full field-proven OD claim.

After real checkpoint, capacity and ground-truth CSVs are collected, seal them into a provenance manifest:

```powershell
$env:PYTHONPATH='backend'
python -m ptis_core.cli seal-field-manifest --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --output data\field_observed\dataset_manifest.json --dataset-id ptis_bengaluru_field_YYYYMMDD --source-name "Manual field survey / agency data source" --source-url "local://data/field_observed" --license "Permissioned validation dataset; publish derived anonymous metrics only" --collection-start YYYY-MM-DD --collection-end YYYY-MM-DD --provenance-contact "Name or team responsible for the dataset"
python -m ptis_core.cli validate-field-data scenarios\silk_board_whitefield.json --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --manifest data\field_observed\dataset_manifest.json
python -m ptis_core.cli run-field-replay scenarios\silk_board_whitefield.json --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --manifest data\field_observed\dataset_manifest.json --output evidence\field_replay_report.json
```

A field claim is allowed only when `field_proven` is `true` in `evidence/field_replay_report.json`.


## Remote Aggregate Replay

If you cannot visit Bengaluru, collect aggregate checkpoint counts through a trusted local observer using `docs/REMOTE_OBSERVER_PACKET.md` and `data/field_observed/templates/remote_aggregate_counts.csv`.

Run:

```powershell
$env:PYTHONPATH='backend'
python -m ptis_core.cli validate-remote-aggregate scenarios\silk_board_whitefield.json --counts data\field_observed\remote_aggregate_counts.csv
python -m ptis_core.cli run-remote-aggregate scenarios\silk_board_whitefield.json --counts data\field_observed\remote_aggregate_counts.csv --output evidence\remote_aggregate_replay_report.json
```

This can support a measured-load capacity-safety claim. It does not unlock `field_proven: true` because it does not contain individual vehicle trajectories or OD labels.

## Official Reference Boundary

The downloaded PDFs in `Real data/` are useful official planning references. They provide aggregate counts and corridor context, including Silk Board, Doddanekundi, Kundalahalli, Tin Factory, ORR and Whitefield references.

They are not event-level field replay data. The project may say "grounded with official Bengaluru planning references," but it must not say "field validated" until checkpoint observations, capacity time series and privacy-reviewed provenance are connected.

## API

Install runtime dependencies first:

```powershell
cd backend
python -m pip install -r requirements.txt
cd ..
$env:PYTHONPATH='backend'
uvicorn ptis_api:app --reload --host 0.0.0.0 --port 8000
```

Endpoints:

- `GET /api/health`
- `GET /api/scenarios`
- `GET /api/corridor`
- `GET /api/evidence/latest`
- `GET /api/evidence/suite`
- `GET /api/evidence/batch`
- `GET /api/evidence/extreme-batch`
- `GET /api/evidence/cctv`
- `GET /api/evidence/field-replay`
- `GET /api/evidence/remote-aggregate`
- `GET /api/official-reference`
- `GET /api/route-geometry`
- `POST /api/scenarios/silk_board_whitefield_capacity_safe_v1/run`
- `POST /api/suite/run`
- `POST /api/batch/run`
- `POST /api/extreme-batch/run`

### No-Dependency Local API

```powershell
$env:PYTHONPATH='backend'
python backend\ptis_dev_server.py
```

This starts a dependency-free verification API on `http://localhost:8000` using the same core engine.

## Dashboard

Serve the repository root as static files:

```powershell
python -m http.server 5173
```

Open `http://localhost:5173/frontend/`.

The dashboard tries the API first, then falls back to local evidence and reference JSON.

## Project Layout

```text
backend/
  ptis_core/          Real algorithm package
  tests/              Unittest verification suite
  ptis_api.py         FastAPI service using the same core
frontend/             Static operations dashboard
scenarios/            Reproducible scenario inputs
evidence/             Generated evidence reports
data/                 Dataset manifests, field CSV templates, and normalized official reference extract
Real data/            Downloaded public PDFs and BMD-45 sample files
docs/                 Architecture, validation and data-intake notes
docker/               Container build files
scripts/              Windows verification helpers
```

## Truth Boundary

The software proof and real CCTV audit are real. The real-world transportation claim still requires live or historical OD/checkpoint data with provenance, calibrated junction counts, branch-road capacity measurements, compliance observations, agency approval for operational actions, and external API/data contracts for navigation-app coordination.

Until those are connected, public language should say "validated on reproducible corridor scenarios, grounded with official planning references, and audited against real Bengaluru CCTV detection data," not "deployed" or "field proven."
