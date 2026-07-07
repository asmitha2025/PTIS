from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from typing import Any

from .bayesian import BayesianDestinationEngine
from .compliance import PIDComplianceController
from .corridor import Corridor
from .decision import SmartLinkDecisionEngine
from .lwr import LWRSolver
from .models import LinkCapacitySnapshot, VehicleObservation, utc_now_iso
from .nav import NavAppShadowModel
from .simulation import load_scenario, scenario_sha256


class BatchSimulator:
    """Deterministic aggregate stress test for the PTIS decision path.

    PTIS does not force a per-vehicle command. It estimates aggregate demand for
    a destination at a decision junction, then activates a capacity-limited link.
    This simulator therefore evaluates aggregate demand estimation and command
    safety rather than pretending every visible vehicle is individually diverted.
    """

    def __init__(self, scenario: dict[str, Any], vehicle_count: int = 240, seed: int = 42) -> None:
        if vehicle_count <= 0:
            raise ValueError("vehicle_count must be positive")
        self.scenario = scenario
        self.vehicle_count = vehicle_count
        self.seed = seed
        self.random = random.Random(seed)
        self.corridor = Corridor.from_dict(scenario["corridor"])
        self.bayesian = BayesianDestinationEngine(self.corridor)
        lwr_cfg = scenario.get("lwr", {})
        self.lwr = LWRSolver(
            n_segments=int(lwr_cfg.get("n_segments", 6)),
            dx_km=float(lwr_cfg.get("dx_km", 0.5)),
            dt_seconds=float(lwr_cfg.get("dt_seconds", 30.0)),
            v_free_kmph=float(lwr_cfg.get("v_free_kmph", 48.0)),
            rho_jam_per_km=float(lwr_cfg.get("rho_jam_per_km", 280.0)),
        )
        self.compliance = PIDComplianceController()
        self.decisions = SmartLinkDecisionEngine()
        nav_cfg = scenario.get("nav_shadow", {})
        self.nav = NavAppShadowModel(
            beta=float(nav_cfg.get("beta", 0.18)),
            app_user_count=float(nav_cfg.get("app_user_count", 1200.0)),
        )
        initial_density = scenario.get("initial_density_tw_per_km") or [0.0] * self.lwr.n_segments
        self.density = [float(value) for value in initial_density]
        self.capacity_by_link = {item["link_id"]: item for item in scenario.get("capacity_snapshots", [])}
        self.target_compliance = float(scenario.get("target_compliance_rate", 0.80))
        self.measured_compliance = float(scenario.get("measured_compliance_rate", 0.78))
        self.approach_flow_vpm = float(scenario.get("approach_flow_vpm", 80.0))
        self.tw_inflow_vpm = float(scenario.get("tw_inflow_vpm", 50.0))
        self.entry_junction_id = scenario.get("batch", {}).get("entry_junction_id", "silk_board")
        self.source = scenario.get("batch", {}).get("source", "anonymous_replay_token")
        self.prior = self.corridor.prior_for_entry(self.entry_junction_id, self.source)
        self.destination_by_order = {
            self.corridor.junction_order(destination.junction_id): destination
            for destination in self.corridor.destinations.values()
        }
        self.link_snapshots: dict[str, list[dict[str, Any]]] = {
            link_id: [] for link_id in self.corridor.smart_links
        }

    def run(self) -> dict[str, Any]:
        vehicles = []
        actual_destination_counts: dict[str, int] = {}

        for index in range(self.vehicle_count):
            actual_destination_id = self._sample_destination()
            actual_destination_counts[actual_destination_id] = actual_destination_counts.get(actual_destination_id, 0) + 1
            vehicle_id = f"BATCH{index:05d}"
            vehicles.append(self._run_vehicle(vehicle_id, actual_destination_id))

        aggregate_decisions = self._aggregate_decisions()
        activations = [item for item in aggregate_decisions if item["decision"]["activate"]]
        capacity_violations = [
            item for item in aggregate_decisions
            if item["decision"]["q_expected_vpm"] - item["decision"]["available_capacity_vpm"] > 1e-9
        ]
        overcommands = [
            item for item in aggregate_decisions
            if item["decision"]["q_expected_vpm"] - item["actual_destination_demand_vpm"] > 1e-9
        ]
        false_positive_activations = [
            item for item in activations if item["actual_destination_demand_vpm"] <= 1e-9
        ]
        activation_confidences = [item["decision"]["confidence"] for item in activations]
        lead_junctions = []
        for item in activations:
            link = self.corridor.smart_links[item["decision"]["link_id"]]
            destination = self.corridor.destinations[link.destination_id]
            lead_junctions.append(
                self.corridor.junction_order(destination.junction_id)
                - self.corridor.junction_order(link.from_junction_id)
            )

        calibration_reports = [
            item["target_calibration"] for item in aggregate_decisions
            if item.get("target_calibration")
        ]
        calibration_abs_errors = [item["absolute_rate_error"] for item in calibration_reports]
        calibration_brier_scores = [item["brier_score"] for item in calibration_reports]
        calibration_ece_values = [item["expected_calibration_error"] for item in calibration_reports]

        metrics = {
            "vehicle_count": self.vehicle_count,
            "observation_count": sum(len(v["observations"]) for v in vehicles),
            "aggregate_decision_count": len(aggregate_decisions),
            "activation_count": len(activations),
            "false_positive_activations": len(false_positive_activations),
            "overcommand_count": len(overcommands),
            "capacity_violation_count": len(capacity_violations),
            "mean_activation_confidence": mean(activation_confidences) if activation_confidences else 0.0,
            "mean_activation_lead_junctions": mean(lead_junctions) if lead_junctions else 0.0,
            "mean_abs_demand_error_vpm": mean([item["abs_demand_error_vpm"] for item in aggregate_decisions]) if aggregate_decisions else 0.0,
            "mean_synthetic_od_abs_rate_error": mean(calibration_abs_errors) if calibration_abs_errors else 0.0,
            "mean_synthetic_od_brier_score": mean(calibration_brier_scores) if calibration_brier_scores else 0.0,
            "mean_synthetic_od_expected_calibration_error": mean(calibration_ece_values) if calibration_ece_values else 0.0,
            "actual_destination_counts": dict(sorted(actual_destination_counts.items())),
        }
        assertions = [
            {
                "name": "aggregate_decisions_exist",
                "passed": metrics["aggregate_decision_count"] > 0,
                "details": {"aggregate_decision_count": metrics["aggregate_decision_count"]},
            },
            {
                "name": "no_capacity_violations",
                "passed": metrics["capacity_violation_count"] == 0,
                "details": {"capacity_violation_count": metrics["capacity_violation_count"]},
            },
            {
                "name": "no_overcommand_vs_actual_destination_demand",
                "passed": metrics["overcommand_count"] == 0,
                "details": {"overcommand_count": metrics["overcommand_count"]},
            },
            {
                "name": "no_false_positive_aggregate_activation",
                "passed": metrics["false_positive_activations"] == 0,
                "details": {"false_positive_activations": metrics["false_positive_activations"]},
            },
            {
                "name": "activations_exist",
                "passed": metrics["activation_count"] > 0,
                "details": {"activation_count": metrics["activation_count"]},
            },
            {
                "name": "synthetic_od_calibration_reported",
                "passed": bool(calibration_reports),
                "details": {
                    "mean_abs_rate_error": metrics["mean_synthetic_od_abs_rate_error"],
                    "mean_brier_score": metrics["mean_synthetic_od_brier_score"],
                    "boundary": "synthetic replay calibration, not field OD accuracy",
                },
            },
            {
                "name": "synthetic_od_rate_error_below_tolerance",
                "passed": metrics["mean_synthetic_od_abs_rate_error"] <= 0.15,
                "details": {
                    "actual": metrics["mean_synthetic_od_abs_rate_error"],
                    "maximum": 0.15,
                    "boundary": "sampling-tolerant synthetic replay check",
                },
            },
        ]
        return {
            "generated_at": utc_now_iso(),
            "scenario_id": self.scenario["id"],
            "scenario_name": self.scenario["name"],
            "vehicle_count": self.vehicle_count,
            "seed": self.seed,
            "metrics": metrics,
            "assertions": assertions,
            "passed": all(item["passed"] for item in assertions),
            "aggregate_decisions": aggregate_decisions,
            "sample_vehicle_traces": vehicles[:10],
        }

    def _run_vehicle(self, vehicle_id: str, actual_destination_id: str) -> dict[str, Any]:
        destination = self.corridor.destinations[actual_destination_id]
        entry_order = self.corridor.junction_order(self.entry_junction_id)
        destination_order = self.corridor.junction_order(destination.junction_id)
        observations = []

        for order in range(entry_order + 1, destination_order + 1):
            destination_at_junction = self.destination_by_order.get(order)
            if destination_at_junction is None:
                continue
            turned = destination_at_junction.id == actual_destination_id
            observation = VehicleObservation(
                vehicle_id=vehicle_id,
                entry_junction_id=self.entry_junction_id if not observations else None,
                junction_id=destination_at_junction.junction_id,
                turned=turned,
                source=self.source,
            )
            state = self.bayesian.update(observation)
            observations.append(observation.__dict__)
            self.density = self.lwr.step(self.density, upstream_inflow_vpm=self.tw_inflow_vpm)
            for link in self.corridor.links_from_junction(observation.junction_id):
                if not turned:
                    self.link_snapshots[link.id].append({
                        "vehicle_id_hash": hashlib.sha256(vehicle_id.encode("utf-8")).hexdigest()[:16],
                        "actual_destination_id": actual_destination_id,
                        "posterior": dict(state.posterior),
                    })
            if turned:
                break

        final_state = self.bayesian.get_state(vehicle_id)
        best_destination_id, best_confidence = final_state.best_destination() if final_state else ("unknown", 0.0)
        return {
            "vehicle_id_hash": hashlib.sha256(vehicle_id.encode("utf-8")).hexdigest()[:16],
            "actual_destination_id": actual_destination_id,
            "best_destination_id": best_destination_id,
            "best_confidence": best_confidence,
            "observations": observations,
        }

    def _aggregate_decisions(self) -> list[dict[str, Any]]:
        compliance_result = self.compliance.update(
            self.target_compliance,
            self.measured_compliance,
            dt_seconds=30.0,
        )
        out = []
        for link_id, snapshots in self.link_snapshots.items():
            if not snapshots:
                continue
            link = self.corridor.smart_links[link_id]
            total = len(snapshots)
            average_posterior = {
                destination_id: sum(s["posterior"].get(destination_id, 0.0) for s in snapshots) / total
                for destination_id in self.corridor.destinations
            }
            flow_scale = self.approach_flow_vpm / total
            estimated_destination_demand_vpm = sum(
                s["posterior"].get(link.destination_id, 0.0) for s in snapshots
            ) * flow_scale
            actual_destination_demand_vpm = sum(
                1 for s in snapshots if s["actual_destination_id"] == link.destination_id
            ) * flow_scale
            link_capacity_cfg = self.capacity_by_link.get(link.id, {})
            mean_density = sum(self.density) / len(self.density)
            nav_load = link_capacity_cfg.get(
                "nav_load_vpm",
                self.nav.predict_vpm(mean_density, self.lwr.rho_jam_per_km),
            )
            capacity = LinkCapacitySnapshot(
                link_id=link.id,
                demand_vpm=float(link_capacity_cfg.get("demand_vpm", estimated_destination_demand_vpm)),
                receiving_capacity_vpm=float(link_capacity_cfg.get("receiving_capacity_vpm", link.capacity_vpm)),
                current_load_vpm=float(link_capacity_cfg.get("current_load_vpm", 0.0)),
                nav_load_vpm=float(nav_load),
            )
            decision = self.decisions.decide(
                average_posterior,
                link,
                capacity,
                compliance_result.command_scale,
            )
            out.append({
                "link_id": link.id,
                "sample_count": total,
                "estimated_destination_demand_vpm": estimated_destination_demand_vpm,
                "actual_destination_demand_vpm": actual_destination_demand_vpm,
                "abs_demand_error_vpm": abs(estimated_destination_demand_vpm - actual_destination_demand_vpm),
                "average_posterior": average_posterior,
                "target_calibration": self._target_calibration(snapshots, link.destination_id),
                "decision": asdict(decision),
            })
        return out

    @staticmethod
    def _target_calibration(
        snapshots: list[dict[str, Any]],
        destination_id: str,
        bin_count: int = 5,
    ) -> dict[str, Any]:
        if not snapshots:
            return {
                "destination_id": destination_id,
                "sample_count": 0,
                "mean_probability": 0.0,
                "observed_rate": 0.0,
                "absolute_rate_error": 0.0,
                "brier_score": 0.0,
                "expected_calibration_error": 0.0,
                "bins": [],
                "boundary": "synthetic replay calibration, not field OD accuracy",
            }

        rows = []
        for snapshot in snapshots:
            probability = float(snapshot["posterior"].get(destination_id, 0.0))
            observed = 1.0 if snapshot["actual_destination_id"] == destination_id else 0.0
            rows.append((probability, observed))

        bins: list[list[tuple[float, float]]] = [[] for _ in range(bin_count)]
        for probability, observed in rows:
            index = min(bin_count - 1, max(0, int(probability * bin_count)))
            bins[index].append((probability, observed))

        bin_reports = []
        expected_calibration_error = 0.0
        total = len(rows)
        for index, values in enumerate(bins):
            if not values:
                continue
            mean_probability = mean([item[0] for item in values])
            observed_rate = mean([item[1] for item in values])
            abs_error = abs(mean_probability - observed_rate)
            expected_calibration_error += (len(values) / total) * abs_error
            bin_reports.append({
                "lower": index / bin_count,
                "upper": (index + 1) / bin_count,
                "count": len(values),
                "mean_probability": mean_probability,
                "observed_rate": observed_rate,
                "absolute_error": abs_error,
            })

        mean_probability = mean([item[0] for item in rows])
        observed_rate = mean([item[1] for item in rows])
        return {
            "destination_id": destination_id,
            "sample_count": total,
            "mean_probability": mean_probability,
            "observed_rate": observed_rate,
            "absolute_rate_error": abs(mean_probability - observed_rate),
            "brier_score": mean([(probability - observed) ** 2 for probability, observed in rows]),
            "expected_calibration_error": expected_calibration_error,
            "bins": bin_reports,
            "boundary": "synthetic replay calibration, not field OD accuracy",
        }

    def _sample_destination(self) -> str:
        r = self.random.random()
        cumulative = 0.0
        last = None
        for destination_id, probability in sorted(self.prior.items()):
            cumulative += probability
            last = destination_id
            if r <= cumulative:
                return destination_id
        if last is None:
            raise ValueError("Cannot sample destination from empty prior")
        return last


def run_batch_file(
    path: str | Path,
    output_path: str | Path | None = None,
    vehicle_count: int = 240,
    seed: int = 42,
) -> dict[str, Any]:
    scenario_path = Path(path)
    report = BatchSimulator(load_scenario(scenario_path), vehicle_count=vehicle_count, seed=seed).run()
    report["scenario_sha256"] = scenario_sha256(scenario_path)
    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report
