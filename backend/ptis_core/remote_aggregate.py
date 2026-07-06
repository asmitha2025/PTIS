from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .compliance import PIDComplianceController
from .corridor import Corridor
from .decision import SmartLinkDecisionEngine
from .models import LinkCapacitySnapshot, utc_now_iso
from .simulation import load_scenario, scenario_sha256

REMOTE_AGGREGATE_FIELDS = [
    "timestamp",
    "checkpoint_id",
    "checkpoint_name",
    "direction",
    "interval_seconds",
    "two_wheeler_count",
    "car_count",
    "auto_count",
    "bus_count",
    "truck_lcv_count",
    "total_count",
    "observer_id",
    "source",
    "weather",
    "notes",
]
COUNT_FIELDS = [
    "two_wheeler_count",
    "car_count",
    "auto_count",
    "bus_count",
    "truck_lcv_count",
]
REMOTE_AGGREGATE_SOURCES = {
    "manual_remote_count",
    "public_permission_video",
    "agency_aggregate",
    "cctv_aggregate",
    "manual_count",
    "unknown",
}
PCU_FACTORS = {
    "two_wheeler_count": 0.5,
    "car_count": 1.0,
    "auto_count": 0.8,
    "bus_count": 3.0,
    "truck_lcv_count": 2.5,
}


def validate_remote_aggregate_counts(
    scenario_path: str | Path,
    counts_path: str | Path,
) -> dict[str, Any]:
    scenario = load_scenario(scenario_path)
    corridor = Corridor.from_dict(scenario["corridor"])
    errors: list[str] = []
    warnings: list[str] = []

    rows = _read_csv(counts_path, REMOTE_AGGREGATE_FIELDS, errors, "remote_aggregate")
    parsed = _validate_rows(rows, corridor, errors, warnings)

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "row_count": len(rows),
            "parsed_row_count": len(parsed),
            "checkpoint_count": len({row["checkpoint_id"] for row in parsed}),
            "total_vehicle_count": sum(row["total_count"] for row in parsed),
        },
        "parsed": {
            "counts": parsed,
        },
    }


def run_remote_aggregate_replay_file(
    scenario_path: str | Path,
    counts_path: str | Path,
    output_path: str | Path | None = None,
    min_rows: int = 30,
    min_duration_minutes: float = 30.0,
) -> dict[str, Any]:
    scenario = load_scenario(scenario_path)
    validation = validate_remote_aggregate_counts(scenario_path, counts_path)
    corridor = Corridor.from_dict(scenario["corridor"])
    report = RemoteAggregateReplayRunner(
        scenario=scenario,
        corridor=corridor,
        rows=validation["parsed"]["counts"],
        validation=validation,
        min_rows=min_rows,
        min_duration_minutes=min_duration_minutes,
    ).run()
    report["scenario_sha256"] = scenario_sha256(scenario_path)
    report["input_sha256"] = {"remote_aggregate_counts": _sha256(counts_path)}

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


class RemoteAggregateReplayRunner:
    def __init__(
        self,
        scenario: dict[str, Any],
        corridor: Corridor,
        rows: list[dict[str, Any]],
        validation: dict[str, Any],
        min_rows: int,
        min_duration_minutes: float,
    ) -> None:
        self.scenario = scenario
        self.corridor = corridor
        self.rows = sorted(rows, key=lambda row: row["_timestamp"])
        self.validation = validation
        self.min_rows = min_rows
        self.min_duration_minutes = min_duration_minutes
        self.decision_engine = SmartLinkDecisionEngine()
        self.compliance = PIDComplianceController()
        self.capacity_by_link = {
            item["link_id"]: item
            for item in scenario.get("capacity_snapshots", [])
            if item.get("link_id")
        }
        self.target_compliance = float(scenario.get("target_compliance_rate", 0.80))
        self.measured_compliance = float(scenario.get("measured_compliance_rate", 0.80))

    def run(self) -> dict[str, Any]:
        compliance_result = self.compliance.update(
            self.target_compliance,
            self.measured_compliance,
            dt_seconds=30.0,
        )
        decisions: list[dict[str, Any]] = []
        capacity_violations = 0
        clamped_windows = 0

        for sequence, row in enumerate(self.rows, start=1):
            links = self.corridor.links_from_junction(row["checkpoint_id"])
            for link in links:
                capacity = self._capacity_for_link(link.id, row["total_vpm"])
                posterior = {link.destination_id: 1.0}
                decision = self.decision_engine.decide(
                    posterior,
                    link,
                    capacity,
                    compliance_result.command_scale,
                )
                if decision.q_expected_vpm - decision.available_capacity_vpm > 1e-9:
                    capacity_violations += 1
                if decision.q_expected_vpm + 1e-9 < max(0.0, capacity.demand_vpm) * max(0.0, compliance_result.command_scale):
                    clamped_windows += 1
                decisions.append({
                    "sequence": sequence,
                    "timestamp": row["timestamp"],
                    "checkpoint_id": row["checkpoint_id"],
                    "link_id": link.id,
                    "assumption": "worst_case_all_observed_flow_targets_managed_destination",
                    "observed_total_vpm": row["total_vpm"],
                    "observed_pcu_vpm": row["pcu_vpm"],
                    "decision": asdict(decision),
                })

        metrics = self._metrics(decisions, capacity_violations, clamped_windows)
        assertions = self._assertions(metrics)
        passed = all(item["passed"] for item in assertions)
        return {
            "generated_at": utc_now_iso(),
            "scenario_id": self.scenario["id"],
            "scenario_name": self.scenario["name"],
            "evidence_type": "remote_aggregate_count_replay",
            "status": "remote_aggregate_replay_passed" if passed else "remote_aggregate_replay_failed",
            "passed": passed,
            "remote_aggregate_replay": passed,
            "field_proven": False,
            "truth_boundary": "Remote aggregate replay checks measured flow and capacity-safety behavior only. It is not field OD validation and cannot prove travel-time reduction, destination accuracy, deployment, or live integration.",
            "assumptions": {
                "destination_pressure": "worst-case: 100% of observed checkpoint flow is treated as managed-link demand for capacity testing",
                "pcu_factors": PCU_FACTORS,
                "pcu_note": "PCU values are a transparent engineering proxy for review, not official field calibration.",
            },
            "metrics": metrics,
            "assertions": assertions,
            "validation": {
                "valid": self.validation["valid"],
                "errors": self.validation["errors"],
                "warnings": self.validation["warnings"],
                "counts": self.validation["counts"],
            },
            "sample_windows": [_public_row(row) for row in self.rows[:20]],
            "sample_decisions": decisions[:20],
        }

    def _capacity_for_link(self, link_id: str, demand_vpm: float) -> LinkCapacitySnapshot:
        link = self.corridor.smart_links[link_id]
        snapshot = self.capacity_by_link.get(link_id, {})
        return LinkCapacitySnapshot(
            link_id=link_id,
            demand_vpm=demand_vpm,
            receiving_capacity_vpm=float(snapshot.get("receiving_capacity_vpm", link.capacity_vpm)),
            current_load_vpm=float(snapshot.get("current_load_vpm", 0.0)),
            nav_load_vpm=float(snapshot.get("nav_load_vpm", 0.0)),
        )

    def _metrics(
        self,
        decisions: list[dict[str, Any]],
        capacity_violations: int,
        clamped_windows: int,
    ) -> dict[str, Any]:
        row_count = len(self.rows)
        duration_minutes = _duration_minutes(self.rows)
        total_vehicle_count = sum(row["total_count"] for row in self.rows)
        total_vpm_values = [row["total_vpm"] for row in self.rows]
        pcu_vpm_values = [row["pcu_vpm"] for row in self.rows]
        activation_count = sum(1 for item in decisions if item["decision"]["activate"])
        managed_checkpoint_count = len({item["checkpoint_id"] for item in decisions})
        return {
            "row_count": row_count,
            "duration_minutes": duration_minutes,
            "checkpoint_count": len({row["checkpoint_id"] for row in self.rows}),
            "managed_checkpoint_count": managed_checkpoint_count,
            "total_vehicle_count": total_vehicle_count,
            "peak_total_vpm": max(total_vpm_values) if total_vpm_values else 0.0,
            "mean_total_vpm": (sum(total_vpm_values) / row_count) if row_count else 0.0,
            "peak_pcu_vpm": max(pcu_vpm_values) if pcu_vpm_values else 0.0,
            "mean_pcu_vpm": (sum(pcu_vpm_values) / row_count) if row_count else 0.0,
            "decision_count": len(decisions),
            "activation_count": activation_count,
            "capacity_violation_count": capacity_violations,
            "clamped_window_count": clamped_windows,
            "field_proven": False,
        }

    def _assertions(self, metrics: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "name": "aggregate_validation_has_no_errors",
                "passed": self.validation["valid"],
                "details": {"errors": self.validation["errors"]},
            },
            {
                "name": "minimum_window_count",
                "passed": metrics["row_count"] >= self.min_rows,
                "details": {"actual": metrics["row_count"], "minimum": self.min_rows},
            },
            {
                "name": "minimum_duration_minutes",
                "passed": metrics["duration_minutes"] >= self.min_duration_minutes,
                "details": {"actual": metrics["duration_minutes"], "minimum": self.min_duration_minutes},
            },
            {
                "name": "managed_link_windows_exist",
                "passed": metrics["decision_count"] > 0,
                "details": {"decision_count": metrics["decision_count"]},
            },
            {
                "name": "capacity_safe_under_worst_case_pressure",
                "passed": metrics["capacity_violation_count"] == 0,
                "details": {"capacity_violation_count": metrics["capacity_violation_count"]},
            },
            {
                "name": "report_does_not_claim_field_proven",
                "passed": not metrics["field_proven"],
                "details": {"field_proven": metrics["field_proven"]},
            },
        ]


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


def _validate_rows(rows: list[dict[str, str]], corridor: Corridor, errors: list[str], warnings: list[str]) -> list[dict[str, Any]]:
    parsed = []
    if not rows:
        errors.append("remote_aggregate:no_rows")
    for index, row in enumerate(rows, start=2):
        checkpoint_id = row.get("checkpoint_id", "")
        if checkpoint_id not in corridor.junctions:
            errors.append(f"remote_aggregate:row_{index}:unknown_checkpoint:{checkpoint_id}")
        elif not corridor.links_from_junction(checkpoint_id):
            warnings.append(f"remote_aggregate:row_{index}:checkpoint_has_no_managed_link:{checkpoint_id}")

        timestamp = _parse_timestamp(row.get("timestamp", ""), errors, f"remote_aggregate:row_{index}")
        interval_seconds = _parse_positive_float(row.get("interval_seconds", ""), errors, f"remote_aggregate:row_{index}:interval_seconds")
        if interval_seconds is not None and interval_seconds > 3600:
            warnings.append(f"remote_aggregate:row_{index}:large_interval_seconds:{interval_seconds}")

        counts = {
            field: _parse_nonnegative_int(row.get(field, ""), errors, f"remote_aggregate:row_{index}:{field}")
            for field in COUNT_FIELDS
        }
        total_count = _parse_nonnegative_int(row.get("total_count", ""), errors, f"remote_aggregate:row_{index}:total_count")
        if all(value is not None for value in counts.values()) and total_count is not None:
            class_sum = sum(counts.values())
            if class_sum != total_count:
                errors.append(f"remote_aggregate:row_{index}:total_count_mismatch:{total_count}!={class_sum}")

        if not row.get("checkpoint_name"):
            errors.append(f"remote_aggregate:row_{index}:missing_checkpoint_name")
        if not row.get("direction"):
            errors.append(f"remote_aggregate:row_{index}:missing_direction")
        if not row.get("observer_id"):
            errors.append(f"remote_aggregate:row_{index}:missing_observer_id")
        source = row.get("source", "")
        if source not in REMOTE_AGGREGATE_SOURCES:
            errors.append(f"remote_aggregate:row_{index}:invalid_source:{source}")

        if timestamp is None or interval_seconds is None or total_count is None or any(value is None for value in counts.values()):
            continue

        pcu_total = sum(counts[field] * PCU_FACTORS[field] for field in COUNT_FIELDS)
        parsed.append({
            "timestamp": row["timestamp"],
            "_timestamp": timestamp,
            "checkpoint_id": checkpoint_id,
            "checkpoint_name": row["checkpoint_name"],
            "direction": row["direction"],
            "interval_seconds": interval_seconds,
            "counts": counts,
            "total_count": total_count,
            "total_vpm": total_count * 60.0 / interval_seconds,
            "pcu_total": pcu_total,
            "pcu_vpm": pcu_total * 60.0 / interval_seconds,
            "observer_id": row["observer_id"],
            "source": source,
            "weather": row.get("weather", ""),
            "notes": row.get("notes", ""),
        })
    return parsed


def _duration_minutes(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    start = min(row["_timestamp"] for row in rows)
    last = max(rows, key=lambda row: row["_timestamp"])
    return ((last["_timestamp"] - start).total_seconds() + float(last["interval_seconds"])) / 60.0


def _public_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "timestamp": row["timestamp"],
        "checkpoint_id": row["checkpoint_id"],
        "checkpoint_name": row["checkpoint_name"],
        "direction": row["direction"],
        "interval_seconds": row["interval_seconds"],
        "counts": row["counts"],
        "total_count": row["total_count"],
        "total_vpm": row["total_vpm"],
        "pcu_vpm": row["pcu_vpm"],
        "source": row["source"],
        "weather": row["weather"],
        "notes": row["notes"],
    }


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


def _parse_positive_float(value: str, errors: list[str], label: str) -> float | None:
    try:
        parsed = float(value)
    except ValueError:
        errors.append(f"{label}:invalid_number:{value}")
        return None
    if parsed <= 0:
        errors.append(f"{label}:non_positive_number:{value}")
        return None
    return parsed


def _parse_nonnegative_int(value: str, errors: list[str], label: str) -> int | None:
    try:
        parsed = int(value)
    except ValueError:
        errors.append(f"{label}:invalid_integer:{value}")
        return None
    if parsed < 0:
        errors.append(f"{label}:negative_integer:{value}")
        return None
    return parsed


def _sha256(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()