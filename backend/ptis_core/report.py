from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .provenance import validate_dataset_manifest
from .simulation import run_scenario_file


def run_suite(scenarios_dir: str | Path, output_path: str | Path | None = None) -> dict[str, Any]:
    scenario_paths = sorted(Path(scenarios_dir).glob("*.json"))
    reports = [run_scenario_file(path) for path in scenario_paths]
    suite = {
        "scenario_count": len(reports),
        "passed_count": sum(1 for report in reports if report["passed"]),
        "failed_count": sum(1 for report in reports if not report["passed"]),
        "passed": all(report["passed"] for report in reports),
        "scenarios": reports,
    }
    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(suite, indent=2, sort_keys=True), encoding="utf-8")
    return suite


def write_proof_report(
    suite_path: str | Path,
    manifest_path: str | Path,
    output_path: str | Path,
    batch_path: str | Path | None = None,
    extreme_batch_path: str | Path | None = None,
    field_replay_path: str | Path | None = None,
    remote_aggregate_path: str | Path | None = None,
    reference_manifest_path: str | Path | None = None,
    reference_extract_path: str | Path | None = None,
    cctv_path: str | Path | None = None,
) -> dict[str, Any]:
    suite = json.loads(Path(suite_path).read_text(encoding="utf-8-sig"))
    dataset = validate_dataset_manifest(manifest_path)
    batch = _read_json_if_exists(batch_path)
    extreme_batch = _read_json_if_exists(extreme_batch_path)
    field_replay = _read_json_if_exists(field_replay_path)
    remote_aggregate = _read_json_if_exists(remote_aggregate_path)
    cctv = _read_json_if_exists(cctv_path)

    reference_manifest = None
    if reference_manifest_path is not None and Path(reference_manifest_path).exists():
        reference_manifest = validate_dataset_manifest(reference_manifest_path)

    reference_extract = _read_json_if_exists(reference_extract_path)

    lines = [
        "# PTIS v2.0 Proof Report",
        "",
        "## Summary",
        "",
        f"- Scenario suite passed: `{suite['passed']}`",
        f"- Scenarios passed: `{suite['passed_count']}/{suite['scenario_count']}`",
        f"- Batch stress test passed: `{batch['passed'] if batch else 'not run'}`",
        f"- Extreme stress test passed: `{extreme_batch['passed'] if extreme_batch else 'not run'}`",
        f"- Real CCTV evidence passed: `{cctv['passed'] if cctv else 'not run'}`",
        f"- Remote aggregate replay passed: `{remote_aggregate['passed'] if remote_aggregate else 'not run'}`",
        f"- Field replay proven: `{field_replay['field_proven'] if field_replay else 'not run'}`",
        f"- Dataset manifest valid: `{dataset['valid']}`",
        f"- Dataset status: `{dataset['status']}`",
        f"- Official reference valid: `{reference_manifest['valid'] if reference_manifest else 'not loaded'}`",
        f"- Official reference status: `{reference_manifest['status'] if reference_manifest else 'not loaded'}`",
        "",
        "## What This Proves",
        "",
        "The current software proof shows that PTIS can process corridor checkpoint observations, update destination probabilities, and make capacity-safe smart-link decisions across positive, negative, deterministic batch, and 8,000-vehicle extreme stress scenarios.",
        "",
        "The real CCTV evidence shows that the project can ingest and audit a public Bengaluru CCTV vehicle-detection dataset sample with COCO annotations, local images, checksums, and explicit source provenance. This supports a vehicle detection/counting layer, not route prediction by itself.",
        "",
        "The official DULT/CMP extract grounds the selected Bengaluru corridor with source-cited planning context and aggregate traffic counts. It does not prove PTIS field performance because it is not an event-level replay dataset.",
        "",
        "Remote aggregate replay, when present, checks observed checkpoint counts against the capacity-safety gate under a worst-case destination-pressure assumption. It is a no-travel validation layer, not OD field proof.",
        "",
        "Field performance is proven only when `evidence/field_replay_report.json` is generated from a field-replay manifest plus observed checkpoint, capacity and label CSV files and all replay assertions pass.",
        "",
        "## Scenario Results",
        "",
        "| Scenario | Passed | Assertions |",
        "|---|---:|---|",
    ]
    for report in suite["scenarios"]:
        assertions = ", ".join(
            f"{item['name']}={'PASS' if item['passed'] else 'FAIL'}"
            for item in report["assertions"]
        )
        lines.append(f"| {report['scenario_name']} | {report['passed']} | {assertions} |")

    if batch:
        lines.extend(_batch_lines(batch, "Batch Stress Test"))

    if extreme_batch:
        lines.extend(_batch_lines(extreme_batch, "Extreme 8,000-Vehicle Stress Test"))

    lines.extend(_cctv_evidence_lines(cctv))
    lines.extend(_remote_aggregate_lines(remote_aggregate))
    lines.extend(_field_replay_lines(field_replay))

    if reference_manifest:
        lines.extend([
            "",
            "## Official Bengaluru Reference",
            "",
            f"- Manifest path: `{reference_manifest['path']}`",
            f"- Valid: `{reference_manifest['valid']}`",
            f"- Status: `{reference_manifest['status']}`",
            f"- Warnings: `{', '.join(reference_manifest['warnings']) or 'none'}`",
        ])
        if reference_extract:
            source_count = len(reference_extract.get("source_documents", []))
            fact_count = len(reference_extract.get("planning_facts", []))
            junction_count = len(reference_extract.get("junction_counts", []))
            screenline_count = len(reference_extract.get("screenline_counts", []))
            lines.extend([
                f"- Source documents: `{source_count}`",
                f"- Planning facts extracted: `{fact_count}`",
                f"- Junction count rows: `{junction_count}`",
                f"- Screen-line count rows: `{screenline_count}`",
                "",
                "Selected extracted values:",
                "",
            ])
            for item in reference_extract.get("junction_counts", [])[:4]:
                lines.append(
                    f"- `{item['name']}`: peak `{item['peak_hour_pcu']}` PCU, 24-hour `{item.get('volume_24h_pcu', 'n/a')}` PCU, `{item['source_table']}` p.{item['pdf_page']}"
                )
            lines.extend([
                "",
                "Reference limitation: official planning reports are not anonymized vehicle trajectories, signal-cycle logs, queue-length time series, or before/after pilot data.",
            ])

    lines.extend([
        "",
        "## Dataset Provenance",
        "",
        f"- Manifest path: `{dataset['path']}`",
        f"- Valid: `{dataset['valid']}`",
        f"- Errors: `{', '.join(dataset['errors']) or 'none'}`",
        f"- Warnings: `{', '.join(dataset['warnings']) or 'none'}`",
        "",
        "## Safe Public Claim",
        "",
        "> PTIS v2.0 now has a reproducible software validation suite, deterministic batch stress test, official Bengaluru planning-reference grounding, a real public Bengaluru CCTV detection-data audit, and a field-replay gate for observed traffic datasets. Field impact remains unclaimed until real observed datasets and agency-controlled pilots are connected and pass the replay gate.",
        "",
        "## Claims Not Allowed Yet",
        "",
        "- Do not claim 43% real-world congestion reduction.",
        "- Do not claim BTP/FASTag/Google integration is live.",
        "- Do not claim deployment or field-proven savings unless `field_proven` is true in `evidence/field_replay_report.json`.",
        "- Do not call synthetic scenario fixtures, CCTV detection data, or official planning references real field replay data.",
    ])
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return {
        "output": str(out),
        "suite_passed": suite["passed"],
        "batch_passed": batch["passed"] if batch else None,
        "extreme_batch_passed": extreme_batch["passed"] if extreme_batch else None,
        "cctv_passed": cctv["passed"] if cctv else None,
        "remote_aggregate_passed": remote_aggregate["passed"] if remote_aggregate else None,
        "field_proven": field_replay["field_proven"] if field_replay else None,
        "dataset_valid": dataset["valid"],
        "reference_valid": reference_manifest["valid"] if reference_manifest else None,
    }


def _batch_lines(batch: dict[str, Any], heading: str) -> list[str]:
    metrics = batch["metrics"]
    lines = [
        "",
        f"## {heading}",
        "",
        f"- Vehicles simulated: `{metrics['vehicle_count']}`",
        f"- Observations processed: `{metrics['observation_count']}`",
        f"- Aggregate decisions evaluated: `{metrics['aggregate_decision_count']}`",
        f"- Activations: `{metrics['activation_count']}`",
        f"- False-positive aggregate activations: `{metrics['false_positive_activations']}`",
        f"- Overcommands versus actual destination demand: `{metrics['overcommand_count']}`",
        f"- Capacity violations: `{metrics['capacity_violation_count']}`",
        f"- Mean activation confidence: `{metrics['mean_activation_confidence']:.4f}`",
        f"- Mean activation lead junctions: `{metrics['mean_activation_lead_junctions']:.2f}`",
        f"- Mean absolute destination-demand error: `{metrics['mean_abs_demand_error_vpm']:.2f} vpm`",
        "",
        "Assertions:",
        "",
    ]
    for assertion in batch["assertions"]:
        lines.append(f"- `{assertion['name']}`: `{'PASS' if assertion['passed'] else 'FAIL'}`")
    return lines

def _cctv_evidence_lines(cctv: dict[str, Any] | None) -> list[str]:
    lines = ["", "## Real CCTV Detection Evidence", ""]
    if not cctv:
        lines.extend([
            "- Status: `not run`",
            "- Expected output: `evidence/cctv_bmd45_report.json`",
            "- Boundary: CCTV detection evidence is separate from field replay proof.",
        ])
        return lines

    metrics = cctv["metrics"]
    lines.extend([
        f"- Passed: `{cctv['passed']}`",
        f"- Evidence type: `{cctv['evidence_type']}`",
        f"- Source: `{cctv['source']['name']}`",
        f"- Source URL: `{cctv['source']['url']}`",
        f"- License: `{cctv['source']['license']}`",
        f"- Metadata rows: `{metrics['metadata_rows']}`",
        f"- COCO images: `{metrics['coco_image_count']}`",
        f"- COCO annotations: `{metrics['coco_annotation_count']}`",
        f"- Vehicle categories in local validation file: `{metrics['category_count']}`",
        f"- Local sample images: `{metrics['local_image_count']}`",
        f"- Local sample annotations: `{metrics['sample_annotation_count']}`",
        "",
        "CCTV truth boundary:",
        "",
        f"> {cctv['truth_boundary']}",
        "",
        "CCTV assertions:",
        "",
    ])
    for assertion in cctv["assertions"]:
        lines.append(f"- `{assertion['name']}`: `{'PASS' if assertion['passed'] else 'FAIL'}`")
    return lines




def _remote_aggregate_lines(remote_aggregate: dict[str, Any] | None) -> list[str]:
    lines = ["", "## Remote Aggregate Replay", ""]
    if not remote_aggregate:
        lines.extend([
            "- Status: `not run`",
            "- Expected output: `evidence/remote_aggregate_replay_report.json`",
            "- Boundary: remote aggregate replay can check measured-load capacity safety, but it is not field OD validation.",
        ])
        return lines

    metrics = remote_aggregate["metrics"]
    lines.extend([
        f"- Passed: `{remote_aggregate['passed']}`",
        f"- Field proven: `{remote_aggregate['field_proven']}`",
        f"- Rows: `{metrics['row_count']}`",
        f"- Duration: `{metrics['duration_minutes']:.2f}` minutes",
        f"- Checkpoints: `{metrics['checkpoint_count']}`",
        f"- Managed checkpoint windows: `{metrics['decision_count']}`",
        f"- Total vehicles counted: `{metrics['total_vehicle_count']}`",
        f"- Peak observed flow: `{metrics['peak_total_vpm']:.2f} vpm`",
        f"- Mean observed flow: `{metrics['mean_total_vpm']:.2f} vpm`",
        f"- Activations under worst-case pressure: `{metrics['activation_count']}`",
        f"- Capacity violations: `{metrics['capacity_violation_count']}`",
        "",
        "Remote aggregate truth boundary:",
        "",
        f"> {remote_aggregate['truth_boundary']}",
        "",
        "Remote aggregate assertions:",
        "",
    ])
    for assertion in remote_aggregate["assertions"]:
        lines.append(f"- `{assertion['name']}`: `{'PASS' if assertion['passed'] else 'FAIL'}`")
    return lines

def _field_replay_lines(field_replay: dict[str, Any] | None) -> list[str]:
    lines = ["", "## Field Replay Gate", ""]
    if not field_replay:
        lines.extend([
            "- Status: `not run`",
            "- Required before field-proven claim: field manifest, vehicle observations CSV, link capacity CSV, and ground-truth labels CSV.",
            "- Output expected at: `evidence/field_replay_report.json`",
        ])
        return lines

    metrics = field_replay["metrics"]
    lines.extend([
        f"- Field proven: `{field_replay['field_proven']}`",
        f"- Observations: `{metrics['observation_count']}`",
        f"- Unique vehicles: `{metrics['unique_vehicle_count']}`",
        f"- Capacity snapshots: `{metrics['capacity_snapshot_count']}`",
        f"- Ground-truth labels: `{metrics['ground_truth_label_count']}`",
        f"- Ground-truth coverage: `{metrics['ground_truth_coverage']:.3f}`",
        f"- Prediction accuracy: `{metrics['prediction_accuracy']:.3f}`",
        f"- Activations: `{metrics['activation_count']}`",
        f"- Capacity violations: `{metrics['capacity_violation_count']}`",
        f"- Capacity fallback count: `{metrics['capacity_fallback_count']}`",
        "",
        "Field replay assertions:",
        "",
    ])
    for assertion in field_replay["assertions"]:
        lines.append(f"- `{assertion['name']}`: `{'PASS' if assertion['passed'] else 'FAIL'}`")
    return lines


def _read_json_if_exists(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    candidate = Path(path)
    if not candidate.exists():
        return None
    return json.loads(candidate.read_text(encoding="utf-8-sig"))
