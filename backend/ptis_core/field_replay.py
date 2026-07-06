from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .bayesian import BayesianDestinationEngine
from .compliance import PIDComplianceController
from .corridor import Corridor
from .decision import SmartLinkDecisionEngine
from .models import LinkCapacitySnapshot, VehicleObservation, utc_now_iso
from .provenance import FIELD_REPLAY_STATUSES, validate_dataset_manifest
from .simulation import load_scenario, scenario_sha256

OBSERVATION_FIELDS = [
    "vehicle_hash",
    "junction_id",
    "timestamp",
    "source",
    "turned",
    "entry_junction_id",
]
CAPACITY_FIELDS = [
    "link_id",
    "timestamp",
    "receiving_capacity_vpm",
    "current_load_vpm",
    "nav_load_vpm",
    "source",
    "observed_approach_flow_vpm",
]
GROUND_TRUTH_FIELDS = ["vehicle_hash", "destination_id", "arrival_timestamp", "source"]
OBSERVATION_SOURCES = {"fastag", "anpr", "manual_count", "cctv_aggregate", "unknown"}
CAPACITY_SOURCES = {"manual_count", "cctv_aggregate", "signal_controller", "agency_log", "unknown"}
GROUND_TRUTH_SOURCES = {"survey", "anpr_exit", "agency_label", "manual_label", "unknown"}
RAW_PLATE_PATTERN = re.compile(r"^[A-Z]{2}[ -]?\d{1,2}[ -]?[A-Z]{1,3}[ -]?\d{3,4}$")
FIELD_SCHEMA_VERSION = "1.0"


def validate_field_data_files(
    scenario_path: str | Path,
    observations_path: str | Path,
    capacity_path: str | Path,
    ground_truth_path: str | Path | None = None,
    manifest_path: str | Path | None = None,
) -> dict[str, Any]:
    scenario = load_scenario(scenario_path)
    corridor = Corridor.from_dict(scenario["corridor"])
    errors: list[str] = []
    warnings: list[str] = []

    manifest = None
    if manifest_path is not None:
        manifest = validate_dataset_manifest(manifest_path)
        if not manifest["valid"]:
            errors.extend(f"manifest:{item}" for item in manifest["errors"])
        if manifest["status"] not in FIELD_REPLAY_STATUSES:
            warnings.append(f"manifest_status_not_field_replay:{manifest['status']}")
    else:
        warnings.append("missing_dataset_manifest")

    observations = _read_csv(observations_path, OBSERVATION_FIELDS, errors, "observations")
    capacities = _read_csv(capacity_path, CAPACITY_FIELDS, errors, "capacity")
    ground_truth = []
    if ground_truth_path is not None:
        ground_truth = _read_csv(ground_truth_path, GROUND_TRUTH_FIELDS, errors, "ground_truth")
    else:
        warnings.append("missing_ground_truth_labels")

    parsed_observations = _validate_observations(observations, corridor, errors, warnings)
    parsed_capacities = _validate_capacities(capacities, corridor, errors, warnings)
    parsed_truth = _validate_ground_truth(ground_truth, corridor, {row["vehicle_hash"] for row in observations}, errors, warnings)

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "manifest": manifest,
        "counts": {
            "observation_rows": len(observations),
            "unique_vehicles": len({row.get("vehicle_hash", "") for row in observations if row.get("vehicle_hash")}),
            "capacity_rows": len(capacities),
            "ground_truth_rows": len(ground_truth),
        },
        "parsed": {
            "observations": parsed_observations,
            "capacities": parsed_capacities,
            "ground_truth": parsed_truth,
        },
    }


def run_field_replay_file(
    scenario_path: str | Path,
    observations_path: str | Path,
    capacity_path: str | Path,
    ground_truth_path: str | Path | None = None,
    manifest_path: str | Path | None = None,
    output_path: str | Path | None = None,
    min_vehicle_count: int = 30,
    min_accuracy: float = 0.60,
    min_ground_truth_coverage: float = 0.20,
) -> dict[str, Any]:
    scenario = load_scenario(scenario_path)
    validation = validate_field_data_files(
        scenario_path,
        observations_path,
        capacity_path,
        ground_truth_path=ground_truth_path,
        manifest_path=manifest_path,
    )
    corridor = Corridor.from_dict(scenario["corridor"])
    report = FieldReplayRunner(
        scenario=scenario,
        corridor=corridor,
        observations=validation["parsed"]["observations"],
        capacities=validation["parsed"]["capacities"],
        ground_truth=validation["parsed"]["ground_truth"],
        validation=validation,
        min_vehicle_count=min_vehicle_count,
        min_accuracy=min_accuracy,
        min_ground_truth_coverage=min_ground_truth_coverage,
    ).run()
    report["scenario_sha256"] = scenario_sha256(scenario_path)
    report["input_sha256"] = {
        "observations": _sha256(observations_path),
        "capacity": _sha256(capacity_path),
        "ground_truth": _sha256(ground_truth_path) if ground_truth_path else None,
        "manifest": _sha256(manifest_path) if manifest_path else None,
    }
    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def compute_field_dataset_checksum(
    observations_path: str | Path,
    capacity_path: str | Path,
    ground_truth_path: str | Path,
) -> str:
    """Stable checksum for the three real replay CSV files as one evidence bundle."""
    digest = hashlib.sha256()
    for label, raw_path in [
        ("observations", observations_path),
        ("capacity", capacity_path),
        ("ground_truth", ground_truth_path),
    ]:
        path = Path(raw_path)
        file_digest = _sha256(path)
        digest.update(f"{label}\0{path.name}\0{file_digest}\n".encode("utf-8"))
    return digest.hexdigest()


def write_field_dataset_manifest(
    template_path: str | Path,
    output_path: str | Path,
    observations_path: str | Path,
    capacity_path: str | Path,
    ground_truth_path: str | Path,
    *,
    dataset_id: str,
    source_name: str,
    source_url: str,
    license_name: str,
    collection_start: str,
    collection_end: str,
    provenance_contact: str,
    privacy_review: str,
    title: str = "PTIS observed field replay dataset for Bengaluru ORR corridor",
    geography: str = "Bengaluru ORR Silk Board to Whitefield corridor",
    notes: str = "Generated after real observed checkpoint, capacity and label CSV files were collected.",
) -> dict[str, Any]:
    template = Path(template_path)
    if template.exists():
        manifest = json.loads(template.read_text(encoding="utf-8-sig"))
    else:
        manifest = {}

    manifest.update({
        "dataset_id": dataset_id,
        "title": title,
        "status": "field_observed",
        "source_name": source_name,
        "source_url": source_url,
        "license": license_name,
        "collection_start": collection_start,
        "collection_end": collection_end,
        "geography": geography,
        "schema_version": FIELD_SCHEMA_VERSION,
        "checksum_sha256": compute_field_dataset_checksum(observations_path, capacity_path, ground_truth_path),
        "provenance_contact": provenance_contact,
        "privacy_review": privacy_review,
        "notes": notes,
    })

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


class FieldReplayRunner:
    def __init__(
        self,
        scenario: dict[str, Any],
        corridor: Corridor,
        observations: list[dict[str, Any]],
        capacities: list[dict[str, Any]],
        ground_truth: dict[str, dict[str, Any]],
        validation: dict[str, Any],
        min_vehicle_count: int,
        min_accuracy: float,
        min_ground_truth_coverage: float,
    ) -> None:
        self.scenario = scenario
        self.corridor = corridor
        self.observations = sorted(observations, key=lambda row: row["_timestamp"])
        self.capacities = _capacity_index(capacities)
        self.ground_truth = ground_truth
        self.validation = validation
        self.min_vehicle_count = min_vehicle_count
        self.min_accuracy = min_accuracy
        self.min_ground_truth_coverage = min_ground_truth_coverage
        engine_cfg = scenario.get("engine", {})
        self.bayesian = BayesianDestinationEngine(
            corridor,
            anpr_epsilon=float(engine_cfg.get("anpr_epsilon", 0.02)),
        )
        self.decision_engine = SmartLinkDecisionEngine()
        self.compliance = PIDComplianceController()
        self.approach_flow_vpm = float(scenario.get("approach_flow_vpm", 80.0))
        self.target_compliance = float(scenario.get("target_compliance_rate", 0.80))
        self.measured_compliance = float(scenario.get("measured_compliance_rate", 0.80))

    def run(self) -> dict[str, Any]:
        decisions: list[dict[str, Any]] = []
        prediction_by_vehicle: dict[str, dict[str, Any]] = {}
        capacity_fallback_count = 0
        observed_flow_fallback_count = 0
        activated_observed_flow_fallback_count = 0
        activation_label_disagreements = 0
        timestamps = [row["_timestamp"] for row in self.observations]

        compliance_result = self.compliance.update(
            self.target_compliance,
            self.measured_compliance,
            dt_seconds=30.0,
        )

        for index, row in enumerate(self.observations, start=1):
            observation = VehicleObservation(
                vehicle_id=row["vehicle_hash"],
                entry_junction_id=row.get("entry_junction_id") or None,
                junction_id=row["junction_id"],
                turned=row["turned"],
                source=row["source"],
                timestamp=row["timestamp"],
            )
            state = self.bayesian.update(observation)
            best_destination_id, best_confidence = state.best_destination()
            prediction_by_vehicle[row["vehicle_hash"]] = {
                "vehicle_hash": row["vehicle_hash"],
                "last_seen": row["timestamp"],
                "best_destination_id": best_destination_id,
                "best_confidence": best_confidence,
                "posterior": dict(sorted(state.posterior.items())),
            }

            for link in self.corridor.links_from_junction(row["junction_id"]):
                capacity_row = _latest_capacity(self.capacities.get(link.id, []), row["_timestamp"])
                if capacity_row is None:
                    capacity_fallback_count += 1
                    capacity = LinkCapacitySnapshot(
                        link_id=link.id,
                        demand_vpm=self.approach_flow_vpm * state.posterior.get(link.destination_id, 0.0),
                        receiving_capacity_vpm=link.capacity_vpm,
                        current_load_vpm=0.0,
                        nav_load_vpm=0.0,
                    )
                    capacity_source = "default_link_config"
                    used_observed_flow = False
                else:
                    observed_flow = capacity_row.get("observed_approach_flow_vpm")
                    used_observed_flow = observed_flow is not None
                    if used_observed_flow:
                        demand_vpm = float(observed_flow) * state.posterior.get(link.destination_id, 0.0)
                    else:
                        observed_flow_fallback_count += 1
                        demand_vpm = self.approach_flow_vpm * state.posterior.get(link.destination_id, 0.0)
                    capacity = LinkCapacitySnapshot(
                        link_id=link.id,
                        demand_vpm=demand_vpm,
                        receiving_capacity_vpm=float(capacity_row["receiving_capacity_vpm"]),
                        current_load_vpm=float(capacity_row["current_load_vpm"]),
                        nav_load_vpm=float(capacity_row["nav_load_vpm"]),
                    )
                    capacity_source = capacity_row["source"]

                decision = self.decision_engine.decide(
                    state.posterior,
                    link,
                    capacity,
                    compliance_result.command_scale,
                )
                truth = self.ground_truth.get(row["vehicle_hash"])
                label_matches_link = None
                if truth is not None:
                    label_matches_link = truth["destination_id"] == link.destination_id
                    if decision.activate and not label_matches_link:
                        activation_label_disagreements += 1
                if decision.activate and not used_observed_flow:
                    activated_observed_flow_fallback_count += 1
                decisions.append({
                    "sequence": index,
                    "timestamp": row["timestamp"],
                    "vehicle_hash": row["vehicle_hash"],
                    "junction_id": row["junction_id"],
                    "link_id": link.id,
                    "capacity_source": capacity_source,
                    "used_observed_approach_flow": used_observed_flow,
                    "label_matches_link_destination": label_matches_link,
                    "decision": asdict(decision),
                })

        metrics = self._metrics(
            prediction_by_vehicle,
            decisions,
            capacity_fallback_count,
            observed_flow_fallback_count,
            activated_observed_flow_fallback_count,
            activation_label_disagreements,
            timestamps,
        )
        assertions = self._assertions(metrics)
        return {
            "generated_at": utc_now_iso(),
            "scenario_id": self.scenario["id"],
            "scenario_name": self.scenario["name"],
            "truth_boundary": "Field proven is true only when a field-replay manifest, observed rows, capacity rows, sufficient labels, accuracy floor, and capacity-safety checks all pass.",
            "field_proven": all(item["passed"] for item in assertions),
            "passed": all(item["passed"] for item in assertions),
            "metrics": metrics,
            "assertions": assertions,
            "validation": {
                "valid": self.validation["valid"],
                "errors": self.validation["errors"],
                "warnings": self.validation["warnings"],
                "counts": self.validation["counts"],
                "manifest": self.validation["manifest"],
            },
            "sample_predictions": list(prediction_by_vehicle.values())[:20],
            "sample_decisions": decisions[:20],
        }

    def _metrics(
        self,
        prediction_by_vehicle: dict[str, dict[str, Any]],
        decisions: list[dict[str, Any]],
        capacity_fallback_count: int,
        observed_flow_fallback_count: int,
        activated_observed_flow_fallback_count: int,
        activation_label_disagreements: int,
        timestamps: list[datetime],
    ) -> dict[str, Any]:
        unique_vehicle_count = len(prediction_by_vehicle)
        labelled = [
            prediction for vehicle_hash, prediction in prediction_by_vehicle.items()
            if vehicle_hash in self.ground_truth
        ]
        correct = [
            prediction for prediction in labelled
            if prediction["best_destination_id"] == self.ground_truth[prediction["vehicle_hash"]]["destination_id"]
        ]
        activations = [item for item in decisions if item["decision"]["activate"]]
        capacity_violations = [
            item for item in decisions
            if item["decision"]["q_expected_vpm"] - item["decision"]["available_capacity_vpm"] > 1e-9
        ]
        return {
            "observation_count": len(self.observations),
            "unique_vehicle_count": unique_vehicle_count,
            "capacity_snapshot_count": sum(len(rows) for rows in self.capacities.values()),
            "ground_truth_label_count": len(self.ground_truth),
            "ground_truth_coverage": (len(labelled) / unique_vehicle_count) if unique_vehicle_count else 0.0,
            "prediction_accuracy": (len(correct) / len(labelled)) if labelled else 0.0,
            "decision_count": len(decisions),
            "activation_count": len(activations),
            "capacity_violation_count": len(capacity_violations),
            "capacity_fallback_count": capacity_fallback_count,
            "observed_flow_fallback_count": observed_flow_fallback_count,
            "activated_observed_flow_fallback_count": activated_observed_flow_fallback_count,
            "activation_label_disagreement_count": activation_label_disagreements,
            "first_observation_timestamp": min(timestamps).isoformat() if timestamps else None,
            "last_observation_timestamp": max(timestamps).isoformat() if timestamps else None,
        }

    def _assertions(self, metrics: dict[str, Any]) -> list[dict[str, Any]]:
        manifest = self.validation.get("manifest")
        manifest_status = manifest["status"] if manifest else None
        assertions = [
            {
                "name": "manifest_allows_field_claim",
                "passed": manifest_status in FIELD_REPLAY_STATUSES,
                "details": {"status": manifest_status, "allowed_statuses": sorted(FIELD_REPLAY_STATUSES)},
            },
            {
                "name": "field_validation_has_no_errors",
                "passed": self.validation["valid"],
                "details": {"errors": self.validation["errors"]},
            },
            {
                "name": "minimum_vehicle_count",
                "passed": metrics["unique_vehicle_count"] >= self.min_vehicle_count,
                "details": {"actual": metrics["unique_vehicle_count"], "minimum": self.min_vehicle_count},
            },
            {
                "name": "capacity_snapshots_exist",
                "passed": metrics["capacity_snapshot_count"] > 0,
                "details": {"capacity_snapshot_count": metrics["capacity_snapshot_count"]},
            },
            {
                "name": "ground_truth_coverage_floor",
                "passed": metrics["ground_truth_coverage"] >= self.min_ground_truth_coverage,
                "details": {"actual": metrics["ground_truth_coverage"], "minimum": self.min_ground_truth_coverage},
            },
            {
                "name": "prediction_accuracy_floor",
                "passed": metrics["prediction_accuracy"] >= self.min_accuracy,
                "details": {"actual": metrics["prediction_accuracy"], "minimum": self.min_accuracy},
            },
            {
                "name": "no_capacity_violations",
                "passed": metrics["capacity_violation_count"] == 0,
                "details": {"capacity_violation_count": metrics["capacity_violation_count"]},
            },
            {
                "name": "no_capacity_fallbacks_for_decisions",
                "passed": metrics["capacity_fallback_count"] == 0,
                "details": {"capacity_fallback_count": metrics["capacity_fallback_count"]},
            },
            {
                "name": "activated_decisions_use_observed_flow",
                "passed": metrics["activated_observed_flow_fallback_count"] == 0,
                "details": {"fallback_count": metrics["activated_observed_flow_fallback_count"]},
            },
        ]
        return assertions


def _read_csv(path: str | Path, required_fields: list[str], errors: list[str], label: str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        errors.append(f"{label}:file_not_found:{csv_path}")
        return []
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            errors.append(f"{label}:missing_header")
            return []
        missing = [field for field in required_fields if field not in reader.fieldnames]
        if missing:
            errors.append(f"{label}:missing_columns:{','.join(missing)}")
            return []
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def _validate_observations(rows: list[dict[str, str]], corridor: Corridor, errors: list[str], warnings: list[str]) -> list[dict[str, Any]]:
    parsed = []
    seen_by_vehicle: dict[str, int] = {}
    if not rows:
        errors.append("observations:no_rows")
    for index, row in enumerate(rows, start=2):
        vehicle_hash = row.get("vehicle_hash", "")
        if not _looks_hashed(vehicle_hash):
            errors.append(f"observations:row_{index}:vehicle_hash_not_anonymized")
        junction_id = row.get("junction_id", "")
        if junction_id not in corridor.junctions:
            errors.append(f"observations:row_{index}:unknown_junction:{junction_id}")
        source = row.get("source", "")
        if source not in OBSERVATION_SOURCES:
            errors.append(f"observations:row_{index}:invalid_source:{source}")
        timestamp = _parse_timestamp(row.get("timestamp", ""), errors, f"observations:row_{index}")
        turned = _parse_bool(row.get("turned", ""), errors, f"observations:row_{index}:turned")
        entry = row.get("entry_junction_id", "")
        if entry and entry not in corridor.junctions:
            errors.append(f"observations:row_{index}:unknown_entry_junction:{entry}")
        if vehicle_hash and vehicle_hash not in seen_by_vehicle and not entry:
            errors.append(f"observations:row_{index}:first_vehicle_row_requires_entry_junction_id")
        if vehicle_hash:
            seen_by_vehicle[vehicle_hash] = seen_by_vehicle.get(vehicle_hash, 0) + 1
        if timestamp is not None and turned is not None:
            parsed.append({
                "vehicle_hash": vehicle_hash,
                "junction_id": junction_id,
                "timestamp": row["timestamp"],
                "_timestamp": timestamp,
                "source": source,
                "turned": turned,
                "entry_junction_id": entry,
            })
    if seen_by_vehicle and len(seen_by_vehicle) < 30:
        warnings.append("small_vehicle_sample_below_default_field_threshold")
    return parsed


def _validate_capacities(rows: list[dict[str, str]], corridor: Corridor, errors: list[str], warnings: list[str]) -> list[dict[str, Any]]:
    parsed = []
    if not rows:
        errors.append("capacity:no_rows")
    for index, row in enumerate(rows, start=2):
        link_id = row.get("link_id", "")
        if link_id not in corridor.smart_links:
            errors.append(f"capacity:row_{index}:unknown_link:{link_id}")
        source = row.get("source", "")
        if source not in CAPACITY_SOURCES:
            errors.append(f"capacity:row_{index}:invalid_source:{source}")
        timestamp = _parse_timestamp(row.get("timestamp", ""), errors, f"capacity:row_{index}")
        values = {}
        for field in ["receiving_capacity_vpm", "current_load_vpm", "nav_load_vpm"]:
            values[field] = _parse_nonnegative_float(row.get(field, ""), errors, f"capacity:row_{index}:{field}")
        observed_flow = None
        if row.get("observed_approach_flow_vpm", ""):
            observed_flow = _parse_nonnegative_float(row.get("observed_approach_flow_vpm", ""), errors, f"capacity:row_{index}:observed_approach_flow_vpm")
        else:
            warnings.append(f"capacity:row_{index}:missing_optional_observed_approach_flow_vpm")
        if timestamp is not None and all(value is not None for value in values.values()):
            parsed.append({
                "link_id": link_id,
                "timestamp": row["timestamp"],
                "_timestamp": timestamp,
                "receiving_capacity_vpm": values["receiving_capacity_vpm"],
                "current_load_vpm": values["current_load_vpm"],
                "nav_load_vpm": values["nav_load_vpm"],
                "observed_approach_flow_vpm": observed_flow,
                "source": source,
            })
    return parsed


def _validate_ground_truth(
    rows: list[dict[str, str]],
    corridor: Corridor,
    observed_vehicle_hashes: set[str],
    errors: list[str],
    warnings: list[str],
) -> dict[str, dict[str, Any]]:
    out = {}
    for index, row in enumerate(rows, start=2):
        vehicle_hash = row.get("vehicle_hash", "")
        if not _looks_hashed(vehicle_hash):
            errors.append(f"ground_truth:row_{index}:vehicle_hash_not_anonymized")
        if vehicle_hash and vehicle_hash not in observed_vehicle_hashes:
            warnings.append(f"ground_truth:row_{index}:vehicle_not_in_observations:{vehicle_hash}")
        destination_id = row.get("destination_id", "")
        if destination_id not in corridor.destinations:
            errors.append(f"ground_truth:row_{index}:unknown_destination:{destination_id}")
        source = row.get("source", "")
        if source not in GROUND_TRUTH_SOURCES:
            errors.append(f"ground_truth:row_{index}:invalid_source:{source}")
        timestamp = _parse_timestamp(row.get("arrival_timestamp", ""), errors, f"ground_truth:row_{index}")
        if timestamp is not None and vehicle_hash:
            out[vehicle_hash] = {
                "vehicle_hash": vehicle_hash,
                "destination_id": destination_id,
                "arrival_timestamp": row["arrival_timestamp"],
                "_timestamp": timestamp,
                "source": source,
            }
    return out


def _parse_timestamp(value: str, errors: list[str], label: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label}:invalid_timestamp:{value}")
        return None
    if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
        errors.append(f"{label}:timestamp_requires_timezone:{value}")
        return None
    return parsed


def _parse_bool(value: str, errors: list[str], label: str) -> bool | None:
    clean = value.strip().lower()
    if clean in {"true", "1", "yes", "y"}:
        return True
    if clean in {"false", "0", "no", "n"}:
        return False
    errors.append(f"{label}:invalid_bool:{value}")
    return None


def _parse_nonnegative_float(value: str, errors: list[str], label: str) -> float | None:
    try:
        parsed = float(value)
    except ValueError:
        errors.append(f"{label}:invalid_number:{value}")
        return None
    if parsed < 0:
        errors.append(f"{label}:negative_number:{value}")
        return None
    return parsed


def _looks_hashed(value: str) -> bool:
    clean = value.strip()
    if len(clean) < 8 or any(char.isspace() for char in clean):
        return False
    if RAW_PLATE_PATTERN.match(clean.upper()):
        return False
    return True


def _capacity_index(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        out.setdefault(row["link_id"], []).append(row)
    for values in out.values():
        values.sort(key=lambda row: row["_timestamp"])
    return out


def _latest_capacity(rows: list[dict[str, Any]], timestamp: datetime) -> dict[str, Any] | None:
    latest = None
    for row in rows:
        if row["_timestamp"] <= timestamp:
            latest = row
        else:
            break
    return latest


def _sha256(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
