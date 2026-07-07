# PTIS

**Predictive Traffic Intelligence System for Bengaluru ORR**

PTIS is a software proof for one simple idea:

> Traffic systems should not only count vehicles. They should infer where traffic pressure is going.

Most traffic systems answer a late question: **how many vehicles are here right now?** PTIS asks an earlier one: **where are these vehicles probably heading?**

A vehicle that keeps crossing checkpoints without turning is giving useful negative evidence. If it passes Silk Board, HSR Layout, Sony World and Marathahalli without exiting, several destinations have effectively been removed from the belief set. PTIS turns that continued movement into a Bayesian destination belief, then checks whether any action is still safe for the receiving road.

This is not presented as a deployed traffic-control system. It is a reproducible software validation project with route grounding, stress replay, official planning references, CCTV detection evidence, and a clear field-validation path.

## Public Demo

- Hugging Face Space: `https://huggingface.co/spaces/Asmitha-28/ptis`
- Live app runtime: `https://asmitha-28-ptis.static.hf.space/`
- Local frontend: `http://127.0.0.1:5173/frontend/index.html`
- Static deploy folder: `deploy/huggingface-space/`

The frontend is a static evidence showcase backed by the same JSON reports produced by the verification pipeline.

## What PTIS Does

PTIS models a road corridor as checkpoints, possible destinations, and capacity-limited smart links.

At each checkpoint, the system updates a destination belief:

```text
P(destination | checkpoint movement)
```

The core loop is:

1. Observe checkpoint movement.
2. Remove destinations that would already have required a turn.
3. Renormalize belief over the remaining destinations.
4. Consider action only when confidence is high enough.
5. Apply a receiving-capacity gate before any activation is allowed.

For the current public scenario, the route is Silk Board to Whitefield on Bengaluru ORR. In the replay evidence, continued movement through Marathahalli raises Whitefield belief to about 67 percent. That is a software replay result, not a field-impact claim.

## What Is Proven

The current repository proves software behavior, not field impact.

Verified today:

- Bayesian destination inference from checkpoint observations.
- Mid-route unknown vehicle handling through reachable-destination priors.
- Low-confidence observations staying inactive.
- Navigation-shadow capacity reservation.
- Full-capacity blocking of otherwise confident activation.
- Compliance scaling without breaking capacity safety.
- 8,000-vehicle stress replay with zero capacity-gate violations.
- Synthetic OD calibration inside the replay harness.
- BMD-45 CCTV detection dataset audit with COCO annotation checks.
- Source-tracked official Bengaluru planning reference extraction.

Generated proof report: `evidence/PROOF_REPORT.md`

## What Is Not Proven Yet

These are intentionally not claimed:

- Live Bengaluru Traffic Police deployment.
- Real-world congestion reduction.
- Google Maps or navigation-app coordination.
- FASTag, number-plate, GPS, or face-based tracking.
- A deployed privacy-preserving vehicle re-identification method.
- Real destination-ground-truth calibration.
- Complete handling of slip roads, service roads, and uninstrumented exits.
- Field replay with observed checkpoint trajectories and destination labels.

This boundary is important. PTIS is strongest when it is described as a software proof with public evidence grounding and a clear path to field validation.

## Reviewer Questions I Expect

### How do you know it is the same vehicle?

In the current proof, same-vehicle movement is represented by synthetic anonymized replay tokens. That lets the Bayesian logic be tested against known generated OD labels.

A real pilot would need one of two approaches:

- privacy-preserving anonymous checkpoint linkage with a measured false-match rate, or
- aggregate flow-conservation from marginal checkpoint counts.

Those are different systems with different error models. PTIS does not claim live GPS, plate, face, or FASTag tracking.

### What about checkpoint gaps?

Checkpoint gaps are a real failure mode. Any uninstrumented slip road, service road, or intermediate exit can leak traffic out of the corridor.

A field pilot must define checkpoint spacing, known exits, missing-sensor assumptions, and uncertainty penalties before claiming OD accuracy.

### Does BMD-45 prove route prediction?

No. BMD-45 supports the vehicle detection/counting evidence layer. It does not contain multi-checkpoint trajectories or OD labels, so it cannot prove destination prediction by itself.

### Is this just OD estimation?

It is related to OD estimation, but the project is focused on the operating loop: checkpoint evidence narrows destination belief, and a capacity gate decides whether action is even eligible. Prediction alone is not the claim. Prediction plus capacity-safe activation boundaries is the system.

## Evidence Snapshot

| Evidence area | Current result |
|---|---:|
| Deterministic scenario suite | 6/6 passed |
| Unit tests | 29/29 passed |
| Standard batch replay | 240 vehicles, 689 observations |
| Extreme stress replay | 8,000 vehicles, 23,314 observations |
| Synthetic OD calibration rate error | about 0.0061 in 8,000-vehicle replay |
| Synthetic OD Brier score | about 0.2226 in 8,000-vehicle replay |
| Capacity-gate violations | 0 |
| False-positive aggregate activations | 0 |
| BMD-45 metadata rows | 10,194 |
| BMD-45 COCO annotations | 106,404 |
| Route geometry | 1,185 OSRM/OpenStreetMap route points |
| Route distance | about 37.9 km |
| Field replay | implemented, waiting for real field CSVs |

The CCTV audit uses the public AIM@IISc BMD-45 Bengaluru Mobility Dataset. It supports detection/counting evidence, not route prediction proof.

## Project Layout

```text
backend/
  ptis_core/
    bayesian.py          Destination-belief update logic
    decision.py          Capacity-safe activation decision logic
    corridor.py          Corridor and checkpoint model
    simulation.py        Scenario replay runner
    batch.py             Batch and stress replay
    field_replay.py      CSV-based field replay gate
    remote_aggregate.py  Remote aggregate-count validation
    cctv_evidence.py     BMD-45 evidence audit
  tests/                 Unit and behavior tests
  ptis_api.py            FastAPI API
  ptis_dev_server.py     Lightweight local API server

frontend/
  index.html             Public showcase
  clear.css              Showcase styling
  clear.js               Evidence loading and MapLibre route rendering
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
  Validation notes, public evidence notes, field-survey notes, and reviewer Q&A
```

## Run Locally

From the repository root:

```powershell
python -m http.server 5173
```

Open:

```text
http://127.0.0.1:5173/frontend/index.html
```

The showcase loads local evidence JSON and route geometry. It uses MapLibre for the route view and falls back to an inline route rendering if map tiles fail.

## Run Verification

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```

This runs the test suite, regenerates the main evidence reports, validates manifests, validates the local BMD-45 sample, and rewrites `evidence/PROOF_REPORT.md`.

Run this before taking screenshots or posting claims publicly.

## Run The API

Install backend dependencies:

```powershell
cd backend
python -m pip install -r requirements.txt
cd ..
```

Start FastAPI:

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

A lightweight dev server is also available:

```powershell
$env:PYTHONPATH='backend'
python backend\ptis_dev_server.py
```

## Field Data Needed Next

To move from software proof to field validation, PTIS needs privacy-safe observed data:

- checkpoint-level movement observations or aggregate counts,
- receiving-capacity time series,
- destination or exit labels where available,
- sensor/observer provenance,
- collection dates and time windows,
- clear permission to publish derived anonymous metrics.

Templates live in `data/field_observed/templates/`.

After collection, seal and validate the field bundle:

```powershell
$env:PYTHONPATH='backend'
python -m ptis_core.cli seal-field-manifest --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --output data\field_observed\dataset_manifest.json --dataset-id ptis_bengaluru_field_YYYYMMDD --source-name "Manual field survey / agency data source" --source-url "local://data/field_observed" --license "Permissioned validation dataset; publish derived anonymous metrics only" --collection-start YYYY-MM-DD --collection-end YYYY-MM-DD --provenance-contact "Name or team responsible for the dataset"
python -m ptis_core.cli validate-field-data scenarios\silk_board_whitefield.json --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --manifest data\field_observed\dataset_manifest.json
python -m ptis_core.cli run-field-replay scenarios\silk_board_whitefield.json --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --manifest data\field_observed\dataset_manifest.json --output evidence\field_replay_report.json
```

## Remote Validation Option

If field collection is not immediately possible, the repo includes a remote observer path:

- `docs/REMOTE_VALIDATION_PATH.md`
- `docs/REMOTE_OBSERVER_PACKET.md`
- `data/field_observed/templates/remote_aggregate_counts.csv`

Remote aggregate counts can test measured-load capacity safety. They still do not prove full OD accuracy because they are aggregate counts, not labeled trajectories.

```powershell
$env:PYTHONPATH='backend'
python -m ptis_core.cli validate-remote-aggregate scenarios\silk_board_whitefield.json --counts data\field_observed\remote_aggregate_counts.csv
python -m ptis_core.cli run-remote-aggregate scenarios\silk_board_whitefield.json --counts data\field_observed\remote_aggregate_counts.csv --output evidence\remote_aggregate_replay_report.json
```

## Safe Public Wording

Good wording:

> PTIS is validated as software on deterministic and stress replay evidence, grounded with official Bengaluru planning references, and audited against public Bengaluru CCTV detection data. The next step is a shadow pilot with real checkpoint observations.

Avoid:

- deployed on ORR,
- BTP integrated,
- Google Maps integrated,
- field proven,
- reduced Bengaluru traffic by X percent.

Those statements are not supported by the current evidence.

## License And Data Notes

Code, generated evidence, third-party datasets, and official public documents are separate. BMD-45 and DULT/CMP references retain their original licenses and provenance. Large raw downloads are not committed unless they are needed for reproducible review.

## Status

PTIS is ready for technical review as a software proof and public evidence showcase. The next meaningful milestone is a privacy-safe field replay dataset or an agency-controlled shadow pilot.
