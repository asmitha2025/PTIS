from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .batch import run_batch_file
from .cctv_evidence import validate_cctv_dataset_sample
from .field_replay import run_field_replay_file, validate_field_data_files, write_field_dataset_manifest
from .provenance import validate_dataset_manifest
from .remote_aggregate import run_remote_aggregate_replay_file, validate_remote_aggregate_counts
from .report import run_suite, write_proof_report
from .simulation import run_scenario_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ptis-core")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run-scenario", help="Run a scenario and emit evidence JSON")
    run_parser.add_argument("scenario", type=Path)
    run_parser.add_argument("--output", type=Path)

    batch_parser = sub.add_parser("run-batch", help="Run deterministic multi-vehicle batch stress test")
    batch_parser.add_argument("scenario", type=Path)
    batch_parser.add_argument("--output", type=Path, default=Path("evidence/batch_report.json"))
    batch_parser.add_argument("--vehicles", type=int, default=240)
    batch_parser.add_argument("--seed", type=int, default=42)

    suite_parser = sub.add_parser("run-suite", help="Run every scenario in a directory")
    suite_parser.add_argument("scenarios_dir", type=Path)
    suite_parser.add_argument("--output", type=Path, default=Path("evidence/suite_report.json"))

    manifest_parser = sub.add_parser("validate-manifest", help="Validate dataset provenance manifest")
    manifest_parser.add_argument("manifest", type=Path)

    cctv_parser = sub.add_parser("validate-cctv-sample", help="Validate BMD-45 CCTV detection sample evidence")
    cctv_parser.add_argument("--sample-root", type=Path, default=Path("Real data/BMD-45-Val"))
    cctv_parser.add_argument("--manifest", type=Path, default=Path("data/bmd45_cctv_manifest.json"))
    cctv_parser.add_argument("--output", type=Path, default=Path("evidence/cctv_bmd45_report.json"))
    cctv_parser.add_argument("--min-local-images", type=int, default=5)

    field_validate = sub.add_parser("validate-field-data", help="Validate field replay CSV files without running the engine")
    field_validate.add_argument("scenario", type=Path)
    field_validate.add_argument("--observations", type=Path, required=True)
    field_validate.add_argument("--capacity", type=Path, required=True)
    field_validate.add_argument("--ground-truth", type=Path)
    field_validate.add_argument("--manifest", type=Path)

    field_replay = sub.add_parser("run-field-replay", help="Replay observed field CSV files through PTIS")
    field_replay.add_argument("scenario", type=Path)
    field_replay.add_argument("--observations", type=Path, required=True)
    field_replay.add_argument("--capacity", type=Path, required=True)
    field_replay.add_argument("--ground-truth", type=Path)
    field_replay.add_argument("--manifest", type=Path)
    field_replay.add_argument("--output", type=Path, default=Path("evidence/field_replay_report.json"))
    field_replay.add_argument("--min-vehicles", type=int, default=30)
    field_replay.add_argument("--min-accuracy", type=float, default=0.60)
    field_replay.add_argument("--min-ground-truth-coverage", type=float, default=0.20)

    seal_manifest = sub.add_parser("seal-field-manifest", help="Write a checksum-sealed manifest for real field replay CSVs")
    seal_manifest.add_argument("--observations", type=Path, required=True)
    seal_manifest.add_argument("--capacity", type=Path, required=True)
    seal_manifest.add_argument("--ground-truth", type=Path, required=True)
    seal_manifest.add_argument("--template", type=Path, default=Path("data/field_dataset_manifest.template.json"))
    seal_manifest.add_argument("--output", type=Path, default=Path("data/field_observed/dataset_manifest.json"))
    seal_manifest.add_argument("--dataset-id", required=True)
    seal_manifest.add_argument("--source-name", required=True)
    seal_manifest.add_argument("--source-url", required=True)
    seal_manifest.add_argument("--license", dest="license_name", required=True)
    seal_manifest.add_argument("--collection-start", required=True)
    seal_manifest.add_argument("--collection-end", required=True)
    seal_manifest.add_argument("--provenance-contact", required=True)
    seal_manifest.add_argument("--privacy-review", default="raw identifiers removed; vehicle IDs salted/hashed before commit; no number plates or FASTag IDs stored")
    seal_manifest.add_argument("--title", default="PTIS observed field replay dataset for Bengaluru ORR corridor")
    seal_manifest.add_argument("--geography", default="Bengaluru ORR Silk Board to Whitefield corridor")
    seal_manifest.add_argument("--notes", default="Generated after real observed checkpoint, capacity and label CSV files were collected.")

    remote_validate = sub.add_parser("validate-remote-aggregate", help="Validate remote aggregate checkpoint-count CSV without making a field-proven claim")
    remote_validate.add_argument("scenario", type=Path)
    remote_validate.add_argument("--counts", type=Path, required=True)

    remote_replay = sub.add_parser("run-remote-aggregate", help="Run remote aggregate-count capacity-safety replay")
    remote_replay.add_argument("scenario", type=Path)
    remote_replay.add_argument("--counts", type=Path, required=True)
    remote_replay.add_argument("--output", type=Path, default=Path("evidence/remote_aggregate_replay_report.json"))
    remote_replay.add_argument("--min-rows", type=int, default=30)
    remote_replay.add_argument("--min-duration-minutes", type=float, default=30.0)

    proof_parser = sub.add_parser("write-proof-report", help="Write Markdown proof report")
    proof_parser.add_argument("--suite", type=Path, default=Path("evidence/suite_report.json"))
    proof_parser.add_argument("--batch", type=Path, default=Path("evidence/batch_report.json"))
    proof_parser.add_argument("--extreme-batch", type=Path, default=Path("evidence/extreme_batch_report.json"))
    proof_parser.add_argument("--field-replay", type=Path, default=Path("evidence/field_replay_report.json"))
    proof_parser.add_argument("--remote-aggregate", type=Path, default=Path("evidence/remote_aggregate_replay_report.json"))
    proof_parser.add_argument("--manifest", type=Path, default=Path("data/dataset_manifest.json"))
    proof_parser.add_argument("--reference-manifest", type=Path, default=Path("data/official_reference_manifest.json"))
    proof_parser.add_argument("--reference-extract", type=Path, default=Path("data/official_reference_bengaluru_cmp_2020.json"))
    proof_parser.add_argument("--cctv", type=Path, default=Path("evidence/cctv_bmd45_report.json"))
    proof_parser.add_argument("--output", type=Path, default=Path("evidence/PROOF_REPORT.md"))

    args = parser.parse_args(argv)
    if args.command == "run-scenario":
        report = run_scenario_file(args.scenario, args.output)
        print(json.dumps({"passed": report["passed"], "assertions": report["assertions"]}, indent=2))
        return 0 if report["passed"] else 2

    if args.command == "run-batch":
        report = run_batch_file(args.scenario, args.output, vehicle_count=args.vehicles, seed=args.seed)
        print(json.dumps({"passed": report["passed"], "metrics": report["metrics"], "assertions": report["assertions"]}, indent=2))
        return 0 if report["passed"] else 2

    if args.command == "run-suite":
        suite = run_suite(args.scenarios_dir, args.output)
        print(json.dumps({"passed": suite["passed"], "passed_count": suite["passed_count"], "scenario_count": suite["scenario_count"]}, indent=2))
        return 0 if suite["passed"] else 2

    if args.command == "validate-manifest":
        result = validate_dataset_manifest(args.manifest)
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 2

    if args.command == "validate-cctv-sample":
        report = validate_cctv_dataset_sample(
            args.sample_root,
            args.manifest,
            output_path=args.output,
            min_local_images=args.min_local_images,
        )
        print(json.dumps({"passed": report["passed"], "metrics": report["metrics"], "assertions": report["assertions"]}, indent=2))
        return 0 if report["passed"] else 2

    if args.command == "validate-field-data":
        result = validate_field_data_files(
            args.scenario,
            args.observations,
            args.capacity,
            ground_truth_path=args.ground_truth,
            manifest_path=args.manifest,
        )
        print(json.dumps({k: v for k, v in result.items() if k != "parsed"}, indent=2))
        return 0 if result["valid"] else 2

    if args.command == "run-field-replay":
        report = run_field_replay_file(
            args.scenario,
            args.observations,
            args.capacity,
            ground_truth_path=args.ground_truth,
            manifest_path=args.manifest,
            output_path=args.output,
            min_vehicle_count=args.min_vehicles,
            min_accuracy=args.min_accuracy,
            min_ground_truth_coverage=args.min_ground_truth_coverage,
        )
        print(json.dumps({"field_proven": report["field_proven"], "metrics": report["metrics"], "assertions": report["assertions"]}, indent=2))
        return 0 if report["field_proven"] else 2

    if args.command == "validate-remote-aggregate":
        result = validate_remote_aggregate_counts(args.scenario, args.counts)
        print(json.dumps({k: v for k, v in result.items() if k != "parsed"}, indent=2))
        return 0 if result["valid"] else 2

    if args.command == "run-remote-aggregate":
        report = run_remote_aggregate_replay_file(
            args.scenario,
            args.counts,
            output_path=args.output,
            min_rows=args.min_rows,
            min_duration_minutes=args.min_duration_minutes,
        )
        print(json.dumps({"passed": report["passed"], "field_proven": report["field_proven"], "metrics": report["metrics"], "assertions": report["assertions"]}, indent=2))
        return 0 if report["passed"] else 2

    if args.command == "seal-field-manifest":
        manifest = write_field_dataset_manifest(
            args.template,
            args.output,
            args.observations,
            args.capacity,
            args.ground_truth,
            dataset_id=args.dataset_id,
            source_name=args.source_name,
            source_url=args.source_url,
            license_name=args.license_name,
            collection_start=args.collection_start,
            collection_end=args.collection_end,
            provenance_contact=args.provenance_contact,
            privacy_review=args.privacy_review,
            title=args.title,
            geography=args.geography,
            notes=args.notes,
        )
        print(json.dumps({"manifest": str(args.output), "checksum_sha256": manifest["checksum_sha256"], "status": manifest["status"]}, indent=2))
        return 0

    if args.command == "write-proof-report":
        result = write_proof_report(
            args.suite,
            args.manifest,
            args.output,
            batch_path=args.batch,
            extreme_batch_path=args.extreme_batch,
            field_replay_path=args.field_replay,
            remote_aggregate_path=args.remote_aggregate,
            reference_manifest_path=args.reference_manifest,
            reference_extract_path=args.reference_extract,
            cctv_path=args.cctv,
        )
        print(json.dumps(result, indent=2))
        return 0

    parser.error(f"Unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
