# PTIS v2.0 Public Evidence Brief

Last updated: 2026-06-26

## Safe Public Claim

PTIS v2.0 is validated as a reproducible software proof for capacity-safe smart-link diversion decisions on a Bengaluru ORR corridor scenario. It is grounded with official Bengaluru mobility planning references and audited against a real public Bengaluru CCTV detection dataset sample.

Do not call it field deployed or field proven yet.

## What Is Proven

| Layer | Evidence | Status |
|---|---|---|
| Software engine | 26 unit/integration tests, 6 scenario cases, 240-vehicle deterministic batch stress test, 8,000-vehicle synthetic extreme stress test | Passed |
| Capacity safety | Smart-link activation refuses to command more demand than available receiving capacity | Passed |
| Negative cases | Low confidence, full capacity, high navigation-shadow load, low compliance, unknown mid-route entry | Passed |
| Official grounding | DULT CMP/CTTP Bengaluru planning references for corridor context | Passed as planning reference |
| Real route visualization | OSRM/OpenStreetMap routed road geometry: 1,185 coordinates over 37.88 km | Passed as map reference |
| Real CCTV audit | IISc AIM BMD-45 validation sample: 10,194 image records, 106,404 COCO annotations, 5 local 1080p frames checked | Passed as detection/counting evidence |
| Remote aggregate replay | Trusted observer aggregate checkpoint-count CSV; measured-load capacity-safety replay; no OD claim | Ready; pending real observer CSV |
| Field replay | Observed checkpoint CSV, capacity CSV, OD/ground-truth CSV, sealed field manifest | Pending |

## What Is Real Data

The project includes a local BMD-45 sample under `Real data/BMD-45-Val/`.

Validated local artifacts:

- `metadata.jsonl`: 10,194 rows
- `_annotations.coco.json`: 10,194 COCO image records and 106,404 annotations
- `images_000/*.png`: 5 local 1920x1080 CCTV sample frames
- `data/bmd45_cctv_manifest.json`: source, license and provenance manifest
- `evidence/cctv_bmd45_report.json`: generated audit report

Boundary: BMD-45 supports vehicle detection/counting evidence. It does not provide anonymized multi-checkpoint trajectories, OD labels, or field replay proof.

## What Is Software Replay

The PTIS replay uses reproducible scenario files in `scenarios/` and generated evidence in `evidence/`.

Core behavior under test:

- update destination posterior after no-turn checkpoint observations;
- trigger smart-link diversion only above the confidence threshold;
- cap commanded diversion by receiving capacity;
- reject unsafe activations under low confidence, full capacity or high navigation-shadow load.

This proves software behavior under the published test suite. It is not a live traffic-control deployment.

## What Is Not Claimed

PTIS does not currently claim:

- live BTP, FASTag, ANPR or Google Maps integration;
- field-measured congestion reduction;
- annual economic savings;
- autonomous signal operation;
- real OD trajectory replay;
- agency-approved deployment.

Those require field-observed or licensed event-level data, privacy review, calibration and agency-controlled pilots.

## Reproduce The Evidence

Run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```

Expected current result:

- 29/29 tests passed
- 6/6 scenarios passed
- 240-vehicle batch stress passed
- 8,000-vehicle extreme stress passed
- BMD-45 CCTV audit passed
- proof report regenerated at `evidence/PROOF_REPORT.md`


## No-Travel Aggregate Replay

If a Bengaluru visit is not possible, use a trusted local observer to fill:

```text
data/field_observed/remote_aggregate_counts.csv
```

Then run:

```powershell
$env:PYTHONPATH='backend'
python -m ptis_core.cli run-remote-aggregate scenarios\silk_board_whitefield.json --counts data\field_observed\remote_aggregate_counts.csv --output evidence\remote_aggregate_replay_report.json
```

This supports only a remote observed aggregate-load safety check. It does not prove OD prediction, travel-time reduction, deployment, or field impact.
## Field-Proven Gate

A field claim is allowed only after real observed field files pass the replay gate:

```text
data/field_observed/vehicle_observations.csv
data/field_observed/link_capacity.csv
data/field_observed/ground_truth_labels.csv
data/field_observed/dataset_manifest.json
```

Required command sequence:

```powershell
$env:PYTHONPATH='backend'
python -m ptis_core.cli seal-field-manifest --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --output data\field_observed\dataset_manifest.json --dataset-id ptis_bengaluru_field_YYYYMMDD --source-name "Manual field survey / agency data source" --source-url "local://data/field_observed" --license "Permissioned validation dataset; publish derived anonymous metrics only" --collection-start YYYY-MM-DD --collection-end YYYY-MM-DD --provenance-contact "Name or team responsible for the dataset"
python -m ptis_core.cli validate-field-data scenarios\silk_board_whitefield.json --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --manifest data\field_observed\dataset_manifest.json
python -m ptis_core.cli run-field-replay scenarios\silk_board_whitefield.json --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --manifest data\field_observed\dataset_manifest.json --output evidence\field_replay_report.json
```

Only when `evidence/field_replay_report.json` contains `field_proven: true` should public language change from field-replay pending to field-replay validated.

## Suggested Reviewer Question

Can checkpoint no-turn observations infer likely destination early enough to trigger a capacity-safe connector-road diversion before a bottleneck forms?

Current answer: yes under the reproducible software scenario suite, baseline batch, and synthetic 8,000-vehicle extreme stress test. Field answer remains pending real checkpoint and OD/ground-truth replay data.