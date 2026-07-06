# Field Survey Runbook

This is the next real evidence step for PTIS. It turns the project from software plus CCTV-audit proof into field-replay proof only if the collected data passes the replay gate.

## Minimum Publishable Packet

Collect one privacy-reviewed dataset for the Bengaluru ORR Silk Board to Whitefield corridor:

- at least 30 unique anonymized vehicles; 100 to 300 is better for public scrutiny
- checkpoint observations at `hsr_layout`, `sony_world`, and `marathahalli`
- final destination labels for at least 20% of observed vehicles
- capacity and approach-flow snapshots for `sl_marathahalli_whitefield`
- collection timestamps with timezone, preferably `+05:30`
- a provenance contact and a written privacy review

Do not claim field validation unless `evidence/field_replay_report.json` says `field_proven: true`.

## Privacy Rule

Never store number plates, FASTag IDs, phone numbers, faces, or raw camera identifiers in this repository.

Recommended vehicle ID flow:

1. Keep the secret salt outside the repository.
2. Hash the raw identifier on the collection device.
3. Store only an anonymized value such as `sha256:<64 hex characters>` in the CSV.
4. Delete or quarantine raw identifiers according to the collection permission.

## Files To Fill

Copy the templates from `data/field_observed/templates/` into `data/field_observed/` and fill the copied files:

```text
data/field_observed/vehicle_observations.csv
data/field_observed/link_capacity.csv
data/field_observed/ground_truth_labels.csv
```

### vehicle_observations.csv

One row per vehicle checkpoint observation.

Required fields:

```csv
vehicle_hash,junction_id,timestamp,source,turned,entry_junction_id
```

Rules:

- The first row for each `vehicle_hash` must include `entry_junction_id`.
- Use `turned=false` when the vehicle continues past that junction.
- Use `turned=true` only when the observed vehicle exits or turns at that junction.
- Allowed `junction_id` values are `silk_board`, `hsr_layout`, `sony_world`, `marathahalli`, `doddanekkundi`, `itpl`, `whitefield`.

### link_capacity.csv

One row per smart-link capacity snapshot.

Required fields:

```csv
link_id,timestamp,receiving_capacity_vpm,current_load_vpm,nav_load_vpm,source,observed_approach_flow_vpm
```

Rules:

- `link_id` is currently `sl_marathahalli_whitefield`.
- `observed_approach_flow_vpm` must be measured from the same time window as the replay decision.
- If activated decisions rely on fallback approach flow, the field gate fails.

### ground_truth_labels.csv

One row per vehicle/session with a known final destination.

Required fields:

```csv
vehicle_hash,destination_id,arrival_timestamp,source
```

Rules:

- `vehicle_hash` must match `vehicle_observations.csv`.
- Allowed `destination_id` values are `hsr_layout`, `sony_world`, `marathahalli`, `doddanekkundi`, `itpl`, `whitefield`.
- Labels can come from a privacy-reviewed survey, exit observation, or agency label.

## Seal The Dataset

After the CSVs are final, generate a checksum-sealed manifest:

```powershell
$env:PYTHONPATH='backend'
python -m ptis_core.cli seal-field-manifest `
  --observations data\field_observed\vehicle_observations.csv `
  --capacity data\field_observed\link_capacity.csv `
  --ground-truth data\field_observed\ground_truth_labels.csv `
  --output data\field_observed\dataset_manifest.json `
  --dataset-id ptis_bengaluru_field_YYYYMMDD `
  --source-name "Manual field survey / agency data source" `
  --source-url "local://data/field_observed" `
  --license "Permissioned validation dataset; publish derived anonymous metrics only" `
  --collection-start YYYY-MM-DD `
  --collection-end YYYY-MM-DD `
  --provenance-contact "Name or team responsible for the dataset"
```

The command writes `checksum_sha256` for the CSV bundle into `data/field_observed/dataset_manifest.json`.

## Validate And Replay

```powershell
$env:PYTHONPATH='backend'
python -m ptis_core.cli validate-field-data scenarios\silk_board_whitefield.json --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --manifest data\field_observed\dataset_manifest.json
python -m ptis_core.cli run-field-replay scenarios\silk_board_whitefield.json --observations data\field_observed\vehicle_observations.csv --capacity data\field_observed\link_capacity.csv --ground-truth data\field_observed\ground_truth_labels.csv --manifest data\field_observed\dataset_manifest.json --output evidence\field_replay_report.json
python -m ptis_core.cli write-proof-report --suite evidence\suite_report.json --batch evidence\batch_report.json --field-replay evidence\field_replay_report.json --manifest data\field_observed\dataset_manifest.json --cctv evidence\cctv_bmd45_report.json --output evidence\PROOF_REPORT.md
```

## Pass Criteria

The public field claim is allowed only when all are true:

- manifest status is `field_observed`, `official_open_data`, or `licensed_partner_data`
- field CSV validation has zero errors
- unique vehicle count meets the configured minimum
- ground-truth coverage meets the configured floor
- prediction accuracy meets the configured floor
- capacity snapshots exist
- capacity violations are zero
- no decisions rely on default capacity fallback
- activated decisions use observed approach flow

If any item fails, the correct public wording remains: software validated, official-reference grounded, CCTV-audited, field replay pending.