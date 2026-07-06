from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

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


def remote_aggregate_placeholder() -> dict:
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


def field_replay_placeholder() -> dict:
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


class PTISHandler(BaseHTTPRequestHandler):
    server_version = "PTISVerificationHTTP/0.1"

    def do_OPTIONS(self) -> None:
        self._send_json({"ok": True})

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json({
                "status": "ok",
                "system": "ptis-v2",
                "mode": "dependency-free-local-verification"
            })
        elif path == "/api/scenarios":
            self._send_json({"scenarios": self._scenarios()})
        elif path == "/api/corridor":
            self._send_json(load_scenario(DEFAULT_SCENARIO)["corridor"])
        elif path == "/api/evidence/latest":
            self._send_json(self._read_or_create(LATEST_EVIDENCE, lambda: run_scenario_file(DEFAULT_SCENARIO, LATEST_EVIDENCE)))
        elif path == "/api/evidence/suite":
            self._send_json(self._read_or_create(SUITE_EVIDENCE, lambda: run_suite(SCENARIOS, SUITE_EVIDENCE)))
        elif path == "/api/evidence/batch":
            self._send_json(self._read_or_create(BATCH_EVIDENCE, lambda: run_batch_file(DEFAULT_SCENARIO, BATCH_EVIDENCE, vehicle_count=240, seed=42)))
        elif path == "/api/evidence/extreme-batch":
            self._send_json(self._read_or_create(EXTREME_BATCH_EVIDENCE, lambda: run_batch_file(DEFAULT_SCENARIO, EXTREME_BATCH_EVIDENCE, vehicle_count=8000, seed=42)))
        elif path == "/api/evidence/cctv":
            self._send_json(self._read_or_create(CCTV_EVIDENCE, lambda: validate_cctv_dataset_sample(BMD45_ROOT, BMD45_MANIFEST, output_path=CCTV_EVIDENCE)))
        elif path == "/api/evidence/remote-aggregate":
            self._send_json(self._read_json_or_placeholder(REMOTE_AGGREGATE_EVIDENCE, remote_aggregate_placeholder))
        elif path == "/api/evidence/field-replay":
            self._send_json(self._read_json_or_placeholder(FIELD_REPLAY_EVIDENCE, field_replay_placeholder))
        elif path == "/api/official-reference":
            self._send_json(json.loads(OFFICIAL_REFERENCE.read_text(encoding="utf-8-sig")))
        elif path == "/api/route-geometry":
            self._send_json(json.loads(ROUTE_GEOMETRY.read_text(encoding="utf-8-sig")))
        else:
            self._send_json({"error": "not found"}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        prefix = "/api/scenarios/"
        suffix = "/run"
        if path.startswith(prefix) and path.endswith(suffix):
            scenario_id = path[len(prefix):-len(suffix)]
            scenario_path = self._scenario_path(scenario_id)
            if scenario_path is None:
                self._send_json({"error": f"unknown scenario: {scenario_id}"}, status=404)
                return
            self._send_json(run_scenario_file(scenario_path, LATEST_EVIDENCE))
            return
        if path == "/api/suite/run":
            self._send_json(run_suite(SCENARIOS, SUITE_EVIDENCE))
            return
        if path == "/api/batch/run":
            self._send_json(run_batch_file(DEFAULT_SCENARIO, BATCH_EVIDENCE, vehicle_count=240, seed=42))
            return
        if path == "/api/extreme-batch/run":
            self._send_json(run_batch_file(DEFAULT_SCENARIO, EXTREME_BATCH_EVIDENCE, vehicle_count=8000, seed=42))
            return
        self._send_json({"error": "not found"}, status=404)

    def log_message(self, format: str, *args) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _scenarios(self) -> list[dict[str, str]]:
        out = []
        for path in sorted(SCENARIOS.glob("*.json")):
            data = load_scenario(path)
            out.append({"id": data["id"], "name": data["name"], "file": path.name})
        return out

    def _scenario_path(self, scenario_id: str) -> Path | None:
        for path in SCENARIOS.glob("*.json"):
            data = load_scenario(path)
            if data["id"] == scenario_id or path.stem == scenario_id:
                return path
        return None

    def _read_or_create(self, path: Path, create):
        if not path.exists():
            return create()
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def _read_json_or_placeholder(self, path: Path, placeholder):
        if not path.exists():
            return placeholder()
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def _send_json(self, payload, status: int = 200) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    server = ThreadingHTTPServer(("0.0.0.0", 8000), PTISHandler)
    print("PTIS verification API listening on http://localhost:8000")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
