# Data Intake Standard

For professional publication, PTIS must distinguish dataset types:

1. `synthetic_verification_fixture`: useful for software validation only.
2. `official_planning_reference`: source-cited reports/planning tables that ground the corridor, but are not event replay data.
3. `official_open_data`: public event-level data with source URL, license, and checksum.
4. `field_observed`: collected sensor/agency data with provenance, privacy review, and checksum.
5. `licensed_partner_data`: non-public data with explicit permission and non-sensitive derived outputs.

## Required Columns for Checkpoint Observations

```csv
vehicle_hash,junction_id,timestamp,source,turned,entry_junction_id
```

Rules:

- `vehicle_hash` must be salted/hashed before storage.
- `timestamp` must include timezone.
- `source` must be one of `fastag`, `anpr`, `manual_count`, `cctv_aggregate`, or `unknown`.
- `turned` must be boolean.
- Raw FASTag IDs or number plates must never be committed.

## Required Capacity Inputs

```csv
link_id,timestamp,receiving_capacity_vpm,current_load_vpm,nav_load_vpm,source,observed_approach_flow_vpm
```

Rules:

- `observed_approach_flow_vpm` should be measured from the same time window as the replay decision.
- If `observed_approach_flow_vpm` is blank, the replay may run with scenario fallback flow, but activated decisions will not pass the field-proven gate.

## Required Ground Truth Labels

```csv
vehicle_hash,destination_id,arrival_timestamp,source
```

Rules:

- Labels are required for prediction accuracy.
- Labels must use the same anonymized `vehicle_hash` as the observation file.
- `destination_id` must be one of the configured scenario destinations.

## Publication Rule

A LinkedIn/GitHub claim may say "grounded with official Bengaluru planning references" when `data/official_reference_manifest.json` validates with status `official_planning_reference`.

A LinkedIn/GitHub claim may say "validated on real field data" only if:

- `data/field_observed/dataset_manifest.json` validates with status `field_observed`, `official_open_data`, or `licensed_partner_data`;
- the real CSV files are sealed with `seal-field-manifest` and pass `validate-field-data`;
- `run-field-replay` produces `evidence/field_replay_report.json`; and
- `field_proven` is `true` in that report.

`official_planning_reference` is not enough for a field-validation claim.
