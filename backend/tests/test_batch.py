import unittest
from pathlib import Path

from ptis_core.batch import run_batch_file


ROOT = Path(__file__).resolve().parents[2]
SCENARIO = ROOT / "scenarios" / "silk_board_whitefield.json"


class BatchSimulationTest(unittest.TestCase):
    def test_batch_stress_report_passes_and_stays_capacity_safe(self):
        report = run_batch_file(SCENARIO, vehicle_count=240, seed=42)
        self.assertTrue(report["passed"])
        metrics = report["metrics"]
        self.assertEqual(metrics["vehicle_count"], 240)
        self.assertEqual(metrics["capacity_violation_count"], 0)
        self.assertEqual(metrics["overcommand_count"], 0)
        self.assertEqual(metrics["false_positive_activations"], 0)
        self.assertGreater(metrics["activation_count"], 0)
        self.assertAlmostEqual(metrics["mean_activation_confidence"], 0.6716417910447768)

    def test_extreme_8000_vehicle_stress_stays_capacity_safe(self):
        report = run_batch_file(SCENARIO, vehicle_count=8000, seed=42)
        self.assertTrue(report["passed"])
        metrics = report["metrics"]
        self.assertEqual(metrics["vehicle_count"], 8000)
        self.assertEqual(metrics["capacity_violation_count"], 0)
        self.assertEqual(metrics["overcommand_count"], 0)
        self.assertEqual(metrics["false_positive_activations"], 0)
        self.assertGreater(metrics["observation_count"], 20000)
        self.assertGreater(metrics["activation_count"], 0)

if __name__ == "__main__":
    unittest.main()
