# Field Replay Validation

This is the step that converts PTIS from software-validated to field-data-validated.

## Required Real Files

Fill copies of the templates in `data/field_observed/templates/`:

1. `vehicle_observations.csv`
   - one row per anonymized vehicle checkpoint observation
   - no number plates, FASTag IDs, phone numbers or raw personal identifiers
   - first row for each `vehicle_hash` must include `entry_junction_id`

2. `link_capacity.csv`
   - one row per smart-link capacity snapshot
   - include `observed_approach_flow_vpm` for each activation window
   - activated decisions fail the field gate if they rely on scenario fallback flow

3. `ground_truth_labels.csv`
   - one row per vehicle/session with observed final destination
   - required for prediction accuracy

4. `data/field_observed/dataset_manifest.json`
   - update only after real data is collected
   - status must be `field_observed`, `official_open_data`, or `licensed_partner_data`
   - generate it with `seal-field-manifest` so the CSV bundle checksum is recorded

## Default Field-Proven Gate

`run-field-replay` defaults to:

- at least 30 unique anonymized vehicles
- at least 20% ground-truth coverage
- at least 60% prediction accuracy
- at least one capacity snapshot
- no capacity violations
- no default capacity fallback for decisions
- activated decisions must use observed approach flow
- manifest status must allow field claims

## Commands

```powershell
$env:PYTHONPATH='backend'
python -m ptis_core.cli seal-field-manifest --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --output data\field_observed\dataset_manifest.json --dataset-id ptis_bengaluru_field_YYYYMMDD --source-name "Manual field survey / agency data source" --source-url "local://data/field_observed" --license "Permissioned validation dataset; publish derived anonymous metrics only" --collection-start YYYY-MM-DD --collection-end YYYY-MM-DD --provenance-contact "Name or team responsible for the dataset"
python -m ptis_core.cli validate-field-data scenarios\silk_board_whitefield.json --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --manifest data\field_observed\dataset_manifest.json
python -m ptis_core.cli run-field-replay scenarios\silk_board_whitefield.json --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --manifest data\field_observed\dataset_manifest.json --output evidence\field_replay_report.json
python -m ptis_core.cli write-proof-report --suite evidence\suite_report.json --batch evidence\batch_report.json --field-replay evidence\field_replay_report.json --manifest data\field_observed\dataset_manifest.json --cctv evidence\cctv_bmd45_report.json --output evidence\PROOF_REPORT.md
```

A public field claim is allowed only when `field_proven` is `true` in `evidence/field_replay_report.json`.
