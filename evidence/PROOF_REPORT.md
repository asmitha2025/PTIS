# PTIS v2.0 Proof Report

## Summary

- Scenario suite passed: `True`
- Scenarios passed: `6/6`
- Batch stress test passed: `True`
- Extreme stress test passed: `True`
- Real CCTV evidence passed: `True`
- Remote aggregate replay passed: `not run`
- Field replay proven: `not run`
- Dataset manifest valid: `True`
- Dataset status: `synthetic_verification_fixture`
- Official reference valid: `True`
- Official reference status: `official_planning_reference`

## What This Proves

The current software proof shows that PTIS can process corridor checkpoint observations, update destination probabilities, and make capacity-safe smart-link decisions across positive, negative, deterministic batch, and 8,000-vehicle extreme stress scenarios.

The real CCTV evidence shows that the project can ingest and audit a public Bengaluru CCTV vehicle-detection dataset sample with COCO annotations, local images, checksums, and explicit source provenance. This supports a vehicle detection/counting layer, not route prediction by itself.

The official DULT/CMP extract grounds the selected Bengaluru corridor with source-cited planning context and aggregate traffic counts. It does not prove PTIS field performance because it is not an event-level replay dataset.

Remote aggregate replay, when present, checks observed checkpoint counts against the capacity-safety gate under a worst-case destination-pressure assumption. It is a no-travel validation layer, not OD field proof.

Field performance is proven only when `evidence/field_replay_report.json` is generated from a field-replay manifest plus observed checkpoint, capacity and label CSV files and all replay assertions pass.

## Scenario Results

| Scenario | Passed | Assertions |
|---|---:|---|
| Full receiving capacity blocks otherwise confident activation | True | capacity_safe_decisions=PASS, expected_link_stays_inactive=PASS, final_best_destination_matches=PASS, final_confidence_floor=PASS |
| Low measured compliance raises command scale without breaking capacity cap | True | expected_link_activates=PASS, activation_confidence_floor=PASS, capacity_safe_decisions=PASS, final_best_destination_matches=PASS, final_confidence_floor=PASS, compliance_command_scale_floor=PASS |
| Low-confidence observation does not activate diversion | True | capacity_safe_decisions=PASS, expected_link_stays_inactive=PASS, final_best_destination_matches=PASS, final_confidence_floor=PASS |
| Mid-route unknown vehicle converges only after downstream observations | True | expected_link_activates=PASS, activation_confidence_floor=PASS, capacity_safe_decisions=PASS, final_best_destination_matches=PASS, final_confidence_floor=PASS |
| Navigation-shadow load reserves capacity and blocks activation | True | capacity_safe_decisions=PASS, expected_link_stays_inactive=PASS, final_best_destination_matches=PASS, final_confidence_floor=PASS |
| Silk Board to Whitefield capacity-safe activation | True | expected_link_activates=PASS, activation_confidence_floor=PASS, capacity_safe_decisions=PASS |

## Batch Stress Test

- Vehicles simulated: `240`
- Observations processed: `689`
- Aggregate decisions evaluated: `1`
- Activations: `1`
- False-positive aggregate activations: `0`
- Overcommands versus actual destination demand: `0`
- Capacity violations: `0`
- Mean activation confidence: `0.6716`
- Mean activation lead junctions: `3.00`
- Mean absolute destination-demand error: `5.95 vpm`

Assertions:

- `aggregate_decisions_exist`: `PASS`
- `no_capacity_violations`: `PASS`
- `no_overcommand_vs_actual_destination_demand`: `PASS`
- `no_false_positive_aggregate_activation`: `PASS`
- `activations_exist`: `PASS`

## Extreme 8,000-Vehicle Stress Test

- Vehicles simulated: `8000`
- Observations processed: `23314`
- Aggregate decisions evaluated: `1`
- Activations: `1`
- False-positive aggregate activations: `0`
- Overcommands versus actual destination demand: `0`
- Capacity violations: `0`
- Mean activation confidence: `0.6716`
- Mean activation lead junctions: `3.00`
- Mean absolute destination-demand error: `0.49 vpm`

Assertions:

- `aggregate_decisions_exist`: `PASS`
- `no_capacity_violations`: `PASS`
- `no_overcommand_vs_actual_destination_demand`: `PASS`
- `no_false_positive_aggregate_activation`: `PASS`
- `activations_exist`: `PASS`

## Real CCTV Detection Evidence

- Passed: `True`
- Evidence type: `real_public_cctv_detection_dataset`
- Source: `AIM@IISc BMD-45 Bengaluru Mobility Dataset`
- Source URL: `https://huggingface.co/datasets/iisc-aim/BMD-45`
- License: `CC BY 4.0`
- Metadata rows: `10194`
- COCO images: `10194`
- COCO annotations: `106404`
- Vehicle categories in local validation file: `13`
- Local sample images: `5`
- Local sample annotations: `40`

CCTV truth boundary:

> BMD-45 validates real Bengaluru CCTV vehicle-detection/counting evidence. It does not provide anonymized vehicle trajectories, OD labels, or checkpoint field replay proof.

CCTV assertions:

- `manifest_valid`: `PASS`
- `manifest_declares_cctv_not_field_replay`: `PASS`
- `metadata_file_exists`: `PASS`
- `annotations_file_exists`: `PASS`
- `metadata_rows_match_coco_images`: `PASS`
- `coco_annotations_present`: `PASS`
- `vehicle_categories_present`: `PASS`
- `local_validation_images_present`: `PASS`
- `local_images_match_metadata_and_coco`: `PASS`
- `local_images_are_1080p_and_match_coco`: `PASS`
- `no_od_or_field_replay_claim`: `PASS`

## Remote Aggregate Replay

- Status: `not run`
- Expected output: `evidence/remote_aggregate_replay_report.json`
- Boundary: remote aggregate replay can check measured-load capacity safety, but it is not field OD validation.

## Field Replay Gate

- Status: `not run`
- Required before field-proven claim: field manifest, vehicle observations CSV, link capacity CSV, and ground-truth labels CSV.
- Output expected at: `evidence/field_replay_report.json`

## Official Bengaluru Reference

- Manifest path: `data\official_reference_manifest.json`
- Valid: `True`
- Status: `official_planning_reference`
- Warnings: `dataset_is_official_reference_not_field_replay`
- Source documents: `2`
- Planning facts extracted: `8`
- Junction count rows: `5`
- Screen-line count rows: `4`

Selected extracted values:

- `Kundalahalli Junction`: peak `5656` PCU, 24-hour `80770` PCU, `Table 2-14` p.80
- `Doddanakundi Junction`: peak `7032` PCU, 24-hour `91960` PCU, `Table 2-14` p.80
- `Silk Board Junction`: peak `18180` PCU, 24-hour `281521` PCU, `Table 2-14` p.80
- `Tin Factory`: peak `16919` PCU, 24-hour `268529` PCU, `Table 2-14` p.80

Reference limitation: official planning reports are not anonymized vehicle trajectories, signal-cycle logs, queue-length time series, or before/after pilot data.

## Dataset Provenance

- Manifest path: `data\dataset_manifest.json`
- Valid: `True`
- Errors: `none`
- Warnings: `dataset_is_synthetic_not_field_data`

## Safe Public Claim

> PTIS v2.0 now has a reproducible software validation suite, deterministic batch stress test, official Bengaluru planning-reference grounding, a real public Bengaluru CCTV detection-data audit, and a field-replay gate for observed traffic datasets. Field impact remains unclaimed until real observed datasets and agency-controlled pilots are connected and pass the replay gate.

## Claims Not Allowed Yet

- Do not claim 43% real-world congestion reduction.
- Do not claim BTP/FASTag/Google integration is live.
- Do not claim deployment or field-proven savings unless `field_proven` is true in `evidence/field_replay_report.json`.
- Do not call synthetic scenario fixtures, CCTV detection data, or official planning references real field replay data.