from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .bayesian import BayesianDestinationEngine
from .compliance import PIDComplianceController
from .corridor import Corridor
from .decision import SmartLinkDecisionEngine
from .lwr import LWRSolver
from .models import (
    CycleAudit,
    LinkCapacitySnapshot,
    VehicleObservation,
    utc_now_iso,
)
from .nav import NavAppShadowModel


class ScenarioRunner:
    def __init__(self, scenario: dict[str, Any]) -> None:
        self.scenario = scenario
        self.corridor = Corridor.from_dict(scenario["corridor"])
        engine_cfg = scenario.get("engine", {})
        self.bayesian = BayesianDestinationEngine(
            self.corridor,
            anpr_epsilon=float(engine_cfg.get("anpr_epsilon", 0.02)),
        )
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
        self.nav_shadow = NavAppShadowModel(
            beta=float(nav_cfg.get("beta", 0.18)),
            app_user_count=float(nav_cfg.get("app_user_count", 1200.0)),
        )
        initial_density = scenario.get("initial_density_tw_per_km")
        if initial_density is None:
            initial_density = [0.0] * self.lwr.n_segments
        self.density = [float(value) for value in initial_density]
        if len(self.density) != self.lwr.n_segments:
            raise ValueError("initial_density_tw_per_km length must match n_segments")

    def run(self) -> dict[str, Any]:
        audits: list[CycleAudit] = []
        capacity_by_link = {
            item["link_id"]: item for item in self.scenario.get("capacity_snapshots", [])
        }
        target_compliance = float(self.scenario.get("target_compliance_rate", 0.80))
        measured_compliance = float(self.scenario.get("measured_compliance_rate", 0.78))
        approach_flow_vpm = float(self.scenario.get("approach_flow_vpm", 80.0))
        tw_inflow_vpm = float(self.scenario.get("tw_inflow_vpm", 50.0))

        for index, raw_observation in enumerate(self.scenario["observations"], start=1):
            observation = VehicleObservation(**raw_observation)
            state = self.bayesian.update(observation)
            self.density = self.lwr.step(self.density, upstream_inflow_vpm=tw_inflow_vpm)
            compliance_result = self.compliance.update(
                target_rate=target_compliance,
                measured_rate=measured_compliance,
                dt_seconds=30.0,
            )
            best_destination_id, best_confidence = state.best_destination()
            link_decisions = []
            for link in self.corridor.links_from_junction(observation.junction_id):
                link_capacity_cfg = capacity_by_link.get(link.id, {})
                mean_density = sum(self.density) / len(self.density)
                nav_load = link_capacity_cfg.get(
                    "nav_load_vpm",
                    self.nav_shadow.predict_vpm(mean_density, self.lwr.rho_jam_per_km),
                )
                destination_demand = approach_flow_vpm * state.posterior.get(
                    link.destination_id, 0.0
                )
                capacity = LinkCapacitySnapshot(
                    link_id=link.id,
                    demand_vpm=float(link_capacity_cfg.get("demand_vpm", destination_demand)),
                    receiving_capacity_vpm=float(
                        link_capacity_cfg.get("receiving_capacity_vpm", link.capacity_vpm)
                    ),
                    current_load_vpm=float(link_capacity_cfg.get("current_load_vpm", 0.0)),
                    nav_load_vpm=float(nav_load),
                )
                decision = self.decisions.decide(
                    posterior=state.posterior,
                    link=link,
                    capacity=capacity,
                    command_scale=compliance_result.command_scale,
                )
                link_decisions.append(asdict(decision))

            audits.append(
                CycleAudit(
                    cycle=index,
                    observation=observation.__dict__,
                    posterior=dict(sorted(state.posterior.items())),
                    best_destination_id=best_destination_id,
                    best_confidence=best_confidence,
                    density_tw_per_km=[round(value, 6) for value in self.density],
                    compliance=asdict(compliance_result),
                    decisions=link_decisions,
                )
            )

        report = {
            "generated_at": utc_now_iso(),
            "scenario_id": self.scenario["id"],
            "scenario_name": self.scenario["name"],
            "corridor": self.corridor.to_public_dict(),
            "cycles": [asdict(audit) for audit in audits],
        }
        report["assertions"] = self._evaluate_assertions(report)
        report["passed"] = all(item["passed"] for item in report["assertions"])
        return report

    def _evaluate_assertions(self, report: dict[str, Any]) -> list[dict[str, Any]]:
        checks = []
        expected = self.scenario.get("expected", {})
        if not expected:
            return checks

        if "activation_link_id" in expected:
            link_id = expected["activation_link_id"]
            activated_cycles = [
                cycle["cycle"]
                for cycle in report["cycles"]
                for decision in cycle["decisions"]
                if decision["link_id"] == link_id and decision["activate"]
            ]
            latest_cycle = expected.get("activation_by_cycle")
            passed = bool(activated_cycles) and (
                latest_cycle is None or min(activated_cycles) <= latest_cycle
            )
            checks.append(
                {
                    "name": "expected_link_activates",
                    "passed": passed,
                    "details": {
                        "link_id": link_id,
                        "activated_cycles": activated_cycles,
                        "activation_by_cycle": latest_cycle,
                    },
                }
            )

        if "min_confidence_at_activation" in expected:
            threshold = float(expected["min_confidence_at_activation"])
            activation_confidences = [
                decision["confidence"]
                for cycle in report["cycles"]
                for decision in cycle["decisions"]
                if decision["activate"]
            ]
            passed = bool(activation_confidences) and min(activation_confidences) >= threshold
            checks.append(
                {
                    "name": "activation_confidence_floor",
                    "passed": passed,
                    "details": {
                        "threshold": threshold,
                        "activation_confidences": activation_confidences,
                    },
                }
            )

        if expected.get("capacity_safe", False):
            violations = [
                {
                    "cycle": cycle["cycle"],
                    "link_id": decision["link_id"],
                    "q_expected_vpm": decision["q_expected_vpm"],
                    "available_capacity_vpm": decision["available_capacity_vpm"],
                }
                for cycle in report["cycles"]
                for decision in cycle["decisions"]
                if decision["q_expected_vpm"] - decision["available_capacity_vpm"] > 1e-9
            ]
            checks.append(
                {
                    "name": "capacity_safe_decisions",
                    "passed": not violations,
                    "details": {"violations": violations},
                }
            )

        if "no_activation_link_id" in expected:
            link_id = expected["no_activation_link_id"]
            activated_cycles = [
                cycle["cycle"]
                for cycle in report["cycles"]
                for decision in cycle["decisions"]
                if decision["link_id"] == link_id and decision["activate"]
            ]
            checks.append(
                {
                    "name": "expected_link_stays_inactive",
                    "passed": not activated_cycles,
                    "details": {
                        "link_id": link_id,
                        "activated_cycles": activated_cycles,
                    },
                }
            )

        if "final_best_destination_id" in expected:
            final_cycle = report["cycles"][-1] if report["cycles"] else {}
            actual = final_cycle.get("best_destination_id")
            checks.append(
                {
                    "name": "final_best_destination_matches",
                    "passed": actual == expected["final_best_destination_id"],
                    "details": {
                        "expected": expected["final_best_destination_id"],
                        "actual": actual,
                    },
                }
            )

        if "min_final_confidence" in expected:
            final_cycle = report["cycles"][-1] if report["cycles"] else {}
            confidence = float(final_cycle.get("best_confidence", 0.0))
            threshold = float(expected["min_final_confidence"])
            checks.append(
                {
                    "name": "final_confidence_floor",
                    "passed": confidence >= threshold,
                    "details": {
                        "threshold": threshold,
                        "actual": confidence,
                    },
                }
            )

        if "min_command_scale" in expected:
            threshold = float(expected["min_command_scale"])
            scales = [
                float(cycle["compliance"].get("command_scale", 0.0))
                for cycle in report["cycles"]
            ]
            checks.append(
                {
                    "name": "compliance_command_scale_floor",
                    "passed": bool(scales) and max(scales) >= threshold,
                    "details": {"threshold": threshold, "scales": scales},
                }
            )
        return checks


def load_scenario(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def scenario_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_scenario_file(path: str | Path, output_path: str | Path | None = None) -> dict[str, Any]:
    scenario_path = Path(path)
    scenario = load_scenario(scenario_path)
    report = ScenarioRunner(scenario).run()
    report["scenario_sha256"] = scenario_sha256(scenario_path)
    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


