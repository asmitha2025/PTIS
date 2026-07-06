import tempfile
import unittest
from pathlib import Path

from ptis_core.remote_aggregate import run_remote_aggregate_replay_file, validate_remote_aggregate_counts


ROOT = Path(__file__).resolve().parents[2]
SCENARIO = ROOT / "scenarios" / "silk_board_whitefield.json"


class RemoteAggregateReplayTest(unittest.TestCase):
    def test_remote_aggregate_replay_passes_capacity_safety_without_field_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            counts = self._write_counts(Path(tmp), checkpoint_id="marathahalli")
            report = run_remote_aggregate_replay_file(
                SCENARIO,
                counts,
                min_rows=3,
                min_duration_minutes=3.0,
            )
            self.assertTrue(report["passed"])
            self.assertTrue(report["remote_aggregate_replay"])
            self.assertFalse(report["field_proven"])
            self.assertEqual(report["metrics"]["row_count"], 3)
            self.assertEqual(report["metrics"]["decision_count"], 3)
            self.assertEqual(report["metrics"]["capacity_violation_count"], 0)
            self.assertGreater(report["metrics"]["peak_total_vpm"], 0)
            self.assertIn("report_does_not_claim_field_proven", {item["name"] for item in report["assertions"]})

    def test_remote_aggregate_validation_rejects_total_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            counts = self._write_counts(Path(tmp), checkpoint_id="marathahalli")
            text = counts.read_text(encoding="utf-8-sig")
            counts.write_text(text.replace(",169,remote_obs_01", ",170,remote_obs_01", 1), encoding="utf-8")
            result = validate_remote_aggregate_counts(SCENARIO, counts)
            self.assertFalse(result["valid"])
            self.assertIn("remote_aggregate:row_2:total_count_mismatch:170!=169", result["errors"])

    def test_remote_aggregate_report_fails_when_checkpoint_has_no_managed_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            counts = self._write_counts(Path(tmp), checkpoint_id="silk_board")
            report = run_remote_aggregate_replay_file(
                SCENARIO,
                counts,
                min_rows=3,
                min_duration_minutes=3.0,
            )
            self.assertFalse(report["passed"])
            self.assertFalse(report["field_proven"])
            failed = {item["name"] for item in report["assertions"] if not item["passed"]}
            self.assertIn("managed_link_windows_exist", failed)
            self.assertIn("checkpoint_has_no_managed_link:silk_board", " ".join(report["validation"]["warnings"]))

    def _write_counts(self, base: Path, checkpoint_id: str) -> Path:
        path = base / "remote_aggregate_counts.csv"
        name = "Marathahalli Bridge" if checkpoint_id == "marathahalli" else "Silk Board"
        rows = [
            "timestamp,checkpoint_id,checkpoint_name,direction,interval_seconds,two_wheeler_count,car_count,auto_count,bus_count,truck_lcv_count,total_count,observer_id,source,weather,notes",
            f"2026-07-03T18:00:00+05:30,{checkpoint_id},{name},toward_whitefield,60,92,44,18,6,9,169,remote_obs_01,manual_remote_count,clear,normal queue",
            f"2026-07-03T18:01:00+05:30,{checkpoint_id},{name},toward_whitefield,60,96,47,19,5,11,178,remote_obs_01,manual_remote_count,clear,queue building",
            f"2026-07-03T18:02:00+05:30,{checkpoint_id},{name},toward_whitefield,60,104,52,21,7,12,196,remote_obs_01,manual_remote_count,clear,heavy queue",
        ]
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        return path


if __name__ == "__main__":
    unittest.main()