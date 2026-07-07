# PTIS: Predictive Traffic Intelligence System

PTIS is a software proof-of-concept for predicting likely traffic destinations on Bengaluru's Outer Ring Road before a bottleneck becomes obvious.

Most traffic systems answer a reactive question: how many vehicles are here right now? PTIS asks an earlier question: where are those vehicles probably going? A vehicle that keeps crossing checkpoints without turning is giving information by elimination. Each passed junction removes one possible destination from the belief set. PTIS turns that movement pattern into a Bayesian destination belief, then checks whether any suggested connector activation is safe against receiving-road capacity.

This repository is intentionally honest about the boundary of proof. It contains a working decision engine, reproducible tests, route-grounded visualization, official planning references, a public Bengaluru CCTV detection-data audit, and field-data templates. It does not claim live Bengaluru Traffic Police deployment, Google Maps integration, FASTag integration, or measured real-world congestion reduction.

## Current Public Claim

A safe public description is:

> PTIS has a reproducible software validation suite, deterministic and 8,000-vehicle stress replay evidence, Bengaluru ORR route grounding, official planning-reference grounding, and a real public Bengaluru CCTV detection-data audit. Field impact remains unclaimed until real checkpoint, capacity, and ground-truth observations are collected through an agency-controlled or trusted observer pilot.

Do not describe this repository as field deployed or field proven unless `evidence/field_replay_report.json` exists and reports `field_proven: true`.

## Demo Links

- Local frontend: `http://127.0.0.1:5173/frontend/index.html`
- Hugging Face Space: `https://huggingface.co/spaces/Asmitha-28/ptis`
- Live app runtime: `https://asmitha-28-ptis.static.hf.space/`
- Static deploy folder: `deploy/huggingface-space/`

The frontend is a static showcase backed by the same evidence JSON files used by the test and reporting pipeline. It is not a mock data page.

## What PTIS Does

PTIS models a corridor as ordered checkpoints and candidate downstream destinations. For each observed vehicle or aggregate observation, the engine updates a belief distribution over reachable destinations.

The central idea is simple:

1. Observe a vehicle or aggregate count crossing a checkpoint.
2. Remove destinations that would already have required a turn or exit.
3. Increase belief in destinations that remain reachable.
4. Consider activation only when confidence is high enough.
5. Apply a receiving-capacity gate before any activation command is allowed.

For the showcase route, the public demo uses Silk Board to Whitefield on Bengaluru ORR. In the replay evidence, continued movement toward Marathahalli raises Whitefield belief to about 67 percent. That is a software replay result, not a field impact claim.

## What Is Proven Today

The repository currently proves these software properties:

- Bayesian destination inference runs from checkpoint observations.
- Mid-route unknown vehicles are handled through reachable-destination priors.
- Low-confidence observations do not trigger unsafe actions.
- Navigation-shadow load can reserve capacity and block activation.
- Full receiving capacity blocks otherwise confident activation.
- Compliance scaling adjusts command pressure without breaking capacity safety.
- Stress replay can process 8,000 simulated vehicles without capacity-gate violations.
- Public Bengaluru CCTV detection evidence can be audited with checksums and COCO annotation counts.
- Official Bengaluru planning references can be normalized into a source-tracked JSON extract.

The generated proof report is available at `evidence/PROOF_REPORT.md`.

## What Is Not Proven Yet

The project does not yet prove:

- Live BTP deployment.
- Real-world congestion reduction.
- Real driver compliance rates.
- Google Maps or navigation-app coordination.
- FASTag or number-plate-based vehicle identity.
- Full origin-destination field accuracy.
- Field replay with observed checkpoint trajectories and ground-truth labels.

This boundary matters. The project is strongest when it is presented as software validation plus public evidence grounding, with field validation clearly listed as the next step.

## Evidence Snapshot

Current repository evidence includes:

| Evidence area | Current result |
|---|---:|
| Deterministic scenario suite | 6/6 passed |
| Unit tests | 29/29 passed in the last full proof run |
| Standard batch stress replay | 240 vehicles, 689 observations |
| Extreme stress replay | 8,000 vehicles, 23,314 observations |
| Capacity-gate violations in stress replay | 0 |
| False-positive aggregate activations | 0 |
| Real CCTV metadata rows | 10,194 |
| Real CCTV COCO image rows | 10,194 |
| Real CCTV COCO annotations | 106,404 |
| Route geometry | 1,185 OSRM/OpenStreetMap route points |
| Route distance | about 37.9 km |
| Field replay | implemented, waiting for real field CSVs |

The CCTV evidence is from the public AIM@IISc BMD-45 Bengaluru Mobility Dataset. It supports the vehicle detection/counting layer, not route prediction by itself, because it does not provide anonymized multi-checkpoint trajectories or OD labels.

## How The System Is Structured

```text
backend/
  ptis_core/
    bayesian.py          Destination-belief update logic
    decision.py          Capacity-safe activation decision logic
    corridor.py          Corridor and checkpoint modeling
    simulation.py        Scenario replay runner
    batch.py             Batch and stress replay
    field_replay.py      CSV-based field replay gate
    remote_aggregate.py  Remote aggregate-count validation path
    cctv_evidence.py     BMD-45 evidence audit
    official_reference.py or related reference readers
  tests/                 Unit and behavioral tests
  ptis_api.py            FastAPI API for dashboard/evidence access
  ptis_dev_server.py     Dependency-light local API server

frontend/
  index.html             Public route-grounded showcase
  clear.css              Polished static UI styling
  clear.js               Evidence loader and MapLibre route rendering
  dashboard.html         Detailed dashboard surface

data/
  orr_silk_board_whitefield_route_osrm.geojson
  official_reference_bengaluru_cmp_2020.json
  bmd45_cctv_manifest.json
  field_observed/templates/

evidence/
  latest_run.json
  suite_report.json
  batch_report.json
  extreme_batch_report.json
  cctv_bmd45_report.json
  PROOF_REPORT.md

docs/
  Architecture, validation, data intake, public evidence, and field survey notes
```

## Running The Project Locally

Start a static server from the repository root:

```powershell
python -m http.server 5173
```

Open:

```text
http://127.0.0.1:5173/frontend/index.html
```

The showcase first tries to load local JSON evidence and route data. It renders the Bengaluru ORR route with MapLibre and falls back to an inline route SVG if the map tiles fail.

## Running The Full Verification Suite

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```

This regenerates the main evidence files and proof report. If you are preparing a public post, run this before taking screenshots or publishing claims.

## Running The API

Install backend dependencies:

```powershell
cd backend
python -m pip install -r requirements.txt
cd ..
```

Start the FastAPI service:

```powershell
$env:PYTHONPATH='backend'
uvicorn ptis_api:app --reload --host 0.0.0.0 --port 8000
```

Useful endpoints:

- `GET /api/health`
- `GET /api/scenarios`
- `GET /api/evidence/latest`
- `GET /api/evidence/suite`
- `GET /api/evidence/batch`
- `GET /api/evidence/extreme-batch`
- `GET /api/evidence/cctv`
- `GET /api/official-reference`
- `GET /api/route-geometry`
- `POST /api/suite/run`
- `POST /api/batch/run`
- `POST /api/extreme-batch/run`

A dependency-light local API is also available:

```powershell
$env:PYTHONPATH='backend'
python backend\ptis_dev_server.py
```

## Field Data Needed For A Stronger Claim

To move from software proof to field validation, PTIS needs privacy-safe observed data such as:

- Checkpoint-level vehicle or aggregate movement observations.
- Link receiving-capacity time series.
- Ground-truth destination or exit labels, if available.
- Sensor or observer provenance.
- Collection dates, time windows, and location definitions.
- A license or permission statement for derived public metrics.

Templates are included in `data/field_observed/templates/`.

After collection, seal and validate the manifest:

```powershell
$env:PYTHONPATH='backend'
python -m ptis_core.cli seal-field-manifest --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --output data\field_observed\dataset_manifest.json --dataset-id ptis_bengaluru_field_YYYYMMDD --source-name "Manual field survey / agency data source" --source-url "local://data/field_observed" --license "Permissioned validation dataset; publish derived anonymous metrics only" --collection-start YYYY-MM-DD --collection-end YYYY-MM-DD --provenance-contact "Name or team responsible for the dataset"
python -m ptis_core.cli validate-field-data scenarios\silk_board_whitefield.json --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --manifest data\field_observed\dataset_manifest.json
python -m ptis_core.cli run-field-replay scenarios\silk_board_whitefield.json --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --manifest data\field_observed\dataset_manifest.json --output evidence\field_replay_report.json
```

## No-Travel Validation Path

If the project owner cannot visit Bengaluru, the repository includes a remote observer packet:

- `docs/REMOTE_VALIDATION_PATH.md`
- `docs/REMOTE_OBSERVER_PACKET.md`
- `data/field_observed/templates/remote_aggregate_counts.csv`

Remote aggregate counts can support a measured-load capacity-safety replay. They still do not prove full OD prediction accuracy because they are aggregate counts rather than individual vehicle trajectories or labeled destinations.

Run remote aggregate validation:

```powershell
$env:PYTHONPATH='backend'
python -m ptis_core.cli validate-remote-aggregate scenarios\silk_board_whitefield.json --counts data\field_observed\remote_aggregate_counts.csv
python -m ptis_core.cli run-remote-aggregate scenarios\silk_board_whitefield.json --counts data\field_observed\remote_aggregate_counts.csv --output evidence\remote_aggregate_replay_report.json
```

## Design And Presentation Notes

The public frontend is designed as a clear evidence showcase rather than a dense internal dashboard. The first screen explains the route-grounded prediction idea, the map grounds the route, and the lower sections separate software proof from field-deployment boundaries.

The color system intentionally uses navy, route blue, and teal so the page reads as a transport/operations tool rather than a playful demo. The UI avoids false claims and keeps the strongest numbers visible without hiding limitations.

## Recommended LinkedIn Boundary

Use language like:

> PTIS is validated as software on deterministic and stress replay evidence, grounded with official Bengaluru planning references, and audited against public Bengaluru CCTV detection data. The next step is a shadow pilot with real checkpoint observations.

Avoid language like:

- "Deployed on ORR"
- "BTP integrated"
- "Google Maps integrated"
- "Field proven"
- "Reduced Bengaluru traffic by X percent"

Those statements are not supported by the current evidence.

## License And Data Notes

The repository code and generated evidence are separate from third-party datasets and official documents. Public references such as BMD-45 and DULT/CMP documents retain their own licenses and provenance. Large local raw data files and downloaded documents are intentionally not committed where they are not needed for reproducible code review.

## Project Status

PTIS is ready for technical review as a software proof and public evidence showcase. The next engineering milestone is a privacy-safe field replay dataset or agency-controlled shadow pilot.
