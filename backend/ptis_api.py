from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ptis_core.batch import run_batch_file
from ptis_core.cctv_evidence import validate_cctv_dataset_sample
from ptis_core.report import run_suite
from ptis_core.simulation import load_scenario, run_scenario_file

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "scenarios"
EVIDENCE = ROOT / "evidence"
DEFAULT_SCENARIO = SCENARIOS / "silk_board_whitefield.json"
LATEST_EVIDENCE = EVIDENCE / "latest_run.json"
SUITE_EVIDENCE = EVIDENCE / "suite_report.json"
BATCH_EVIDENCE = EVIDENCE / "batch_report.json"
EXTREME_BATCH_EVIDENCE = EVIDENCE / "extreme_batch_report.json"
CCTV_EVIDENCE = EVIDENCE / "cctv_bmd45_report.json"
FIELD_REPLAY_EVIDENCE = EVIDENCE / "field_replay_report.json"
REMOTE_AGGREGATE_EVIDENCE = EVIDENCE / "remote_aggregate_replay_report.json"
OFFICIAL_REFERENCE = ROOT / "data" / "official_reference_bengaluru_cmp_2020.json"
ROUTE_GEOMETRY = ROOT / "data" / "orr_silk_board_whitefield_route_osrm.geojson"
BMD45_ROOT = ROOT / "Real data" / "BMD-45-Val"
BMD45_MANIFEST = ROOT / "data" / "bmd45_cctv_manifest.json"

app = FastAPI(
    title="PTIS v2.0 Verification API",
    version="0.1.0",
    description="Production-oriented local verification API for PTIS core algorithms.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "system": "ptis-v2",
        "mode": "local-verification",
        "truth_policy": "no live integration claims without real credentials and data feeds",
    }


@app.get("/api/scenarios")
def list_scenarios() -> dict[str, list[dict[str, str]]]:
    scenarios = []
    for path in sorted(SCENARIOS.glob("*.json")):
        data = load_scenario(path)
        scenarios.append({"id": data["id"], "name": data["name"], "file": path.name})
    return {"scenarios": scenarios}


@app.get("/api/corridor")
def corridor() -> dict:
    scenario = load_scenario(DEFAULT_SCENARIO)
    return scenario["corridor"]


@app.post("/api/scenarios/{scenario_id}/run")
def run_scenario(scenario_id: str) -> dict:
    path = _scenario_path(scenario_id)
    return run_scenario_file(path, LATEST_EVIDENCE)


@app.post("/api/suite/run")
def run_scenario_suite() -> dict:
    return run_suite(SCENARIOS, SUITE_EVIDENCE)


@app.post("/api/batch/run")
def run_batch() -> dict:
    return run_batch_file(DEFAULT_SCENARIO, BATCH_EVIDENCE, vehicle_count=240, seed=42)


@app.post("/api/extreme-batch/run")
def run_extreme_batch() -> dict:
    return run_batch_file(DEFAULT_SCENARIO, EXTREME_BATCH_EVIDENCE, vehicle_count=8000, seed=42)


@app.get("/api/evidence/latest")
def latest_evidence() -> dict:
    if not LATEST_EVIDENCE.exists():
        return run_scenario_file(DEFAULT_SCENARIO, LATEST_EVIDENCE)
    return json.loads(LATEST_EVIDENCE.read_text(encoding="utf-8-sig"))


@app.get("/api/evidence/suite")
def suite_evidence() -> dict:
    if not SUITE_EVIDENCE.exists():
        return run_suite(SCENARIOS, SUITE_EVIDENCE)
    return json.loads(SUITE_EVIDENCE.read_text(encoding="utf-8-sig"))


@app.get("/api/evidence/batch")
def batch_evidence() -> dict:
    if not BATCH_EVIDENCE.exists():
        return run_batch_file(DEFAULT_SCENARIO, BATCH_EVIDENCE, vehicle_count=240, seed=42)
    return json.loads(BATCH_EVIDENCE.read_text(encoding="utf-8-sig"))


@app.get("/api/evidence/extreme-batch")
def extreme_batch_evidence() -> dict:
    if not EXTREME_BATCH_EVIDENCE.exists():
        return run_batch_file(DEFAULT_SCENARIO, EXTREME_BATCH_EVIDENCE, vehicle_count=8000, seed=42)
    return json.loads(EXTREME_BATCH_EVIDENCE.read_text(encoding="utf-8-sig"))


@app.get("/api/evidence/cctv")
def cctv_evidence() -> dict:
    if not CCTV_EVIDENCE.exists():
        return validate_cctv_dataset_sample(BMD45_ROOT, BMD45_MANIFEST, output_path=CCTV_EVIDENCE)
    return json.loads(CCTV_EVIDENCE.read_text(encoding="utf-8-sig"))



@app.get("/api/evidence/remote-aggregate")
def remote_aggregate_evidence() -> dict:
    if not REMOTE_AGGREGATE_EVIDENCE.exists():
        return _remote_aggregate_placeholder()
    return json.loads(REMOTE_AGGREGATE_EVIDENCE.read_text(encoding="utf-8-sig"))

@app.get("/api/evidence/field-replay")
def field_replay_evidence() -> dict:
    if not FIELD_REPLAY_EVIDENCE.exists():
        return _field_replay_placeholder()
    return json.loads(FIELD_REPLAY_EVIDENCE.read_text(encoding="utf-8-sig"))


@app.get("/api/official-reference")
def official_reference() -> dict:
    return json.loads(OFFICIAL_REFERENCE.read_text(encoding="utf-8-sig"))


@app.get("/api/route-geometry")
def route_geometry() -> dict:
    return json.loads(ROUTE_GEOMETRY.read_text(encoding="utf-8-sig"))


def _scenario_path(scenario_id: str) -> Path:
    for path in SCENARIOS.glob("*.json"):
        data = load_scenario(path)
        if data["id"] == scenario_id or path.stem == scenario_id:
            return path
    raise HTTPException(status_code=404, detail=f"Unknown scenario: {scenario_id}")




def _remote_aggregate_placeholder() -> dict:
    return {
        "field_proven": False,
        "passed": False,
        "remote_aggregate_replay": False,
        "status": "waiting_for_remote_aggregate_counts",
        "truth_boundary": "Remote aggregate replay requires observed aggregate checkpoint counts. It checks measured-load capacity safety only and does not prove field OD behavior.",
        "metrics": {
            "row_count": 0,
            "duration_minutes": 0.0,
            "checkpoint_count": 0,
            "decision_count": 0,
            "total_vehicle_count": 0,
            "peak_total_vpm": 0.0,
            "mean_total_vpm": 0.0,
            "capacity_violation_count": 0,
        },
        "assertions": [
            {"name": "remote_aggregate_report_exists", "passed": False, "details": {"expected_path": str(REMOTE_AGGREGATE_EVIDENCE)}}
        ],
    }

def _field_replay_placeholder() -> dict:
    return {
        "field_proven": False,
        "passed": False,
        "status": "waiting_for_field_replay_data",
        "truth_boundary": "Field proof requires observed checkpoint CSV, link capacity CSV, ground-truth labels CSV, and a checksum-sealed field/partner/open-data manifest.",
        "metrics": {
            "observation_count": 0,
            "unique_vehicle_count": 0,
            "capacity_snapshot_count": 0,
            "ground_truth_label_count": 0,
            "ground_truth_coverage": 0.0,
            "prediction_accuracy": 0.0,
            "activation_count": 0,
            "capacity_violation_count": 0,
        },
        "assertions": [
            {"name": "field_replay_report_exists", "passed": False, "details": {"expected_path": str(FIELD_REPLAY_EVIDENCE)}}
        ],
    }
