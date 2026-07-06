import json
import tempfile
import unittest
from pathlib import Path

from ptis_core.field_replay import run_field_replay_file, validate_field_data_files, write_field_dataset_manifest
from ptis_core.provenance import validate_dataset_manifest


ROOT = Path(__file__).resolve().parents[2]
SCENARIO = ROOT / "scenarios" / "silk_board_whitefield.json"


class FieldReplayTest(unittest.TestCase):
    def test_field_replay_passes_when_observed_inputs_meet_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            observations, capacity, truth, manifest = self._write_valid_field_files(base, vehicle_count=4)
            report = run_field_replay_file(
                SCENARIO,
                observations,
                capacity,
                ground_truth_path=truth,
                manifest_path=manifest,
                min_vehicle_count=4,
                min_accuracy=0.75,
                min_ground_truth_coverage=1.0,
            )
            self.assertTrue(report["field_proven"])
            self.assertEqual(report["metrics"]["unique_vehicle_count"], 4)
            self.assertEqual(report["metrics"]["capacity_violation_count"], 0)
            self.assertEqual(report["metrics"]["capacity_fallback_count"], 0)
            self.assertEqual(report["metrics"]["prediction_accuracy"], 1.0)

    def test_field_replay_fails_without_ground_truth_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            observations, capacity, _truth, manifest = self._write_valid_field_files(base, vehicle_count=4)
            report = run_field_replay_file(
                SCENARIO,
                observations,
                capacity,
                manifest_path=manifest,
                min_vehicle_count=4,
                min_accuracy=0.75,
                min_ground_truth_coverage=1.0,
            )
            self.assertFalse(report["field_proven"])
            failed = {item["name"] for item in report["assertions"] if not item["passed"]}
            self.assertIn("ground_truth_coverage_floor", failed)
            self.assertIn("prediction_accuracy_floor", failed)

    def test_validation_rejects_raw_plate_like_vehicle_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            observations, capacity, truth, manifest = self._write_valid_field_files(base, vehicle_count=1)
            text = observations.read_text(encoding="utf-8-sig")
            observations.write_text(text.replace("vh_00000000", "KA01AB1234"), encoding="utf-8")
            result = validate_field_data_files(SCENARIO, observations, capacity, ground_truth_path=truth, manifest_path=manifest)
            self.assertFalse(result["valid"])
            self.assertIn("observations:row_2:vehicle_hash_not_anonymized", result["errors"])

    def test_capacity_schema_requires_observed_flow_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            observations, capacity, truth, manifest = self._write_valid_field_files(base, vehicle_count=4)
            capacity.write_text(
                "link_id,timestamp,receiving_capacity_vpm,current_load_vpm,nav_load_vpm,source\n"
                "sl_marathahalli_whitefield,2026-06-24T08:00:00+05:30,23.0,8.0,0.5,manual_count\n",
                encoding="utf-8",
            )
            result = validate_field_data_files(SCENARIO, observations, capacity, ground_truth_path=truth, manifest_path=manifest)
            self.assertFalse(result["valid"])
            self.assertIn("capacity:missing_columns:observed_approach_flow_vpm", result["errors"])

    def test_write_field_dataset_manifest_seals_real_csv_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            observations, capacity, truth, _manifest = self._write_valid_field_files(base, vehicle_count=4)
            manifest = base / "field_dataset_manifest.json"
            generated = write_field_dataset_manifest(
                ROOT / "data" / "field_dataset_manifest.template.json",
                manifest,
                observations,
                capacity,
                truth,
                dataset_id="ptis_field_test_2026_06_24",
                source_name="manual field survey dry run",
                source_url="local://unit-test-field-bundle",
                license_name="private validation fixture",
                collection_start="2026-06-24",
                collection_end="2026-06-24",
                provenance_contact="unit test",
                privacy_review="raw identifiers removed before storage; anonymized vehicle hashes only",
            )
            self.assertEqual(generated["status"], "field_observed")
            self.assertRegex(generated["checksum_sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue(validate_dataset_manifest(manifest)["valid"])

            report = run_field_replay_file(
                SCENARIO,
                observations,
                capacity,
                ground_truth_path=truth,
                manifest_path=manifest,
                min_vehicle_count=4,
                min_accuracy=0.75,
                min_ground_truth_coverage=1.0,
            )
            self.assertTrue(report["field_proven"])

    def _write_valid_field_files(self, base: Path, vehicle_count: int):
        observations = base / "vehicle_observations.csv"
        capacity = base / "link_capacity.csv"
        truth = base / "ground_truth_labels.csv"
        manifest = base / "manifest.json"

        obs_lines = ["vehicle_hash,junction_id,timestamp,source,turned,entry_junction_id"]
        truth_lines = ["vehicle_hash,destination_id,arrival_timestamp,source"]
        for index in range(vehicle_count):
            vehicle = f"vh_{index:08d}"
            minute = 10 + index
            obs_lines.extend([
                f"{vehicle},hsr_layout,2026-06-24T08:{minute:02d}:00+05:30,fastag,false,silk_board",
                f"{vehicle},sony_world,2026-06-24T08:{minute:02d}:30+05:30,fastag,false,",
                f"{vehicle},marathahalli,2026-06-24T08:{minute+1:02d}:00+05:30,fastag,false,",
            ])
            truth_lines.append(f"{vehicle},whitefield,2026-06-24T08:{minute+10:02d}:00+05:30,survey")
        observations.write_text("\n".join(obs_lines) + "\n", encoding="utf-8")
        capacity.write_text(
            "link_id,timestamp,receiving_capacity_vpm,current_load_vpm,nav_load_vpm,source,observed_approach_flow_vpm\n"
            "sl_marathahalli_whitefield,2026-06-24T08:00:00+05:30,23.0,8.0,0.5,manual_count,80.0\n",
            encoding="utf-8",
        )
        truth.write_text("\n".join(truth_lines) + "\n", encoding="utf-8")
        manifest.write_text(json.dumps({
            "dataset_id": "field_test_dataset",
            "title": "Temporary field replay test dataset",
            "status": "field_observed",
            "source_name": "unit test",
            "source_url": "local://unit-test",
            "license": "test fixture",
            "collection_start": "2026-06-24",
            "collection_end": "2026-06-24",
            "geography": "Bengaluru ORR Silk Board to Whitefield corridor",
            "schema_version": "1.0",
            "checksum_sha256": "test-fixture-checksum",
            "provenance_contact": "unit test",
            "privacy_review": "synthetic temporary hashed IDs only for test runtime",
        }), encoding="utf-8")
        return observations, capacity, truth, manifest


if __name__ == "__main__":
    unittest.main()

