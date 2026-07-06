# Field Observed Data Kit

Copy these templates before filling them. Do not edit the originals.

Use `docs/FIELD_SURVEY_RUNBOOK.md` before collecting or publishing field data.

## Files Required For A Field-Proven Claim

1. `vehicle_observations.csv`
   - One row per anonymized vehicle checkpoint observation.
   - `vehicle_hash` must be salted/hashed before storage.
   - `entry_junction_id` is required on the first row for each vehicle.
   - `turned` is `true` only when the observed vehicle exits/turns at that junction.

2. `link_capacity.csv`
   - One row per link/time capacity snapshot.
   - `observed_approach_flow_vpm` should come from real counted approach flow. If left blank, the replay can run but the field-proven gate fails for activated decisions.

3. `ground_truth_labels.csv`
   - One row per labelled vehicle/session destination.
   - Required to measure prediction accuracy.

## Allowed IDs For Current Scenario

Junction IDs:

- `silk_board`
- `hsr_layout`
- `sony_world`
- `marathahalli`
- `doddanekkundi`
- `itpl`
- `whitefield`

Destination IDs:

- `hsr_layout`
- `sony_world`
- `marathahalli`
- `doddanekkundi`
- `itpl`
- `whitefield`

Smart link IDs:

- `sl_marathahalli_whitefield`

## Minimum Default Gate

The default field-proven gate requires:

- dataset manifest status: `field_observed`, `official_open_data`, or `licensed_partner_data`
- at least 30 unique anonymized vehicles
- at least 20% ground-truth label coverage
- at least 60% destination prediction accuracy
- at least one capacity snapshot
- no capacity violations
- no default-capacity fallback for decisions
- activated decisions must use observed approach flow

## Commands

```powershell
$env:PYTHONPATH='backend'
python -m ptis_core.cli seal-field-manifest --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --output data\field_observed\dataset_manifest.json --dataset-id ptis_bengaluru_field_YYYYMMDD --source-name "Manual field survey / agency data source" --source-url "local://data/field_observed" --license "Permissioned validation dataset; publish derived anonymous metrics only" --collection-start YYYY-MM-DD --collection-end YYYY-MM-DD --provenance-contact "Name or team responsible for the dataset"
python -m ptis_core.cli validate-field-data scenarios\silk_board_whitefield.json --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --manifest data\field_observed\dataset_manifest.json
python -m ptis_core.cli run-field-replay scenarios\silk_board_whitefield.json --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --manifest data\field_observed\dataset_manifest.json --output evidence\field_replay_report.json
```
