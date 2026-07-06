import unittest
from pathlib import Path

from ptis_core.report import run_suite
from ptis_core.simulation import run_scenario_file


ROOT = Path(__file__).resolve().parents[2]
SCENARIO = ROOT / "scenarios" / "silk_board_whitefield.json"
SCENARIOS_DIR = ROOT / "scenarios"


class ScenarioSimulationTest(unittest.TestCase):
    def test_silk_board_whitefield_scenario_passes_all_assertions(self):
        report = run_scenario_file(SCENARIO)
        self.assertTrue(report["passed"])
        self.assertEqual([item["passed"] for item in report["assertions"]], [True, True, True])

        cycle3 = report["cycles"][2]
        self.assertEqual(cycle3["best_destination_id"], "whitefield")
        decision = cycle3["decisions"][0]
        self.assertTrue(decision["activate"])
        self.assertAlmostEqual(decision["confidence"], 0.6716417910447762)
        self.assertLessEqual(decision["q_expected_vpm"], decision["available_capacity_vpm"])

    def test_all_published_scenarios_pass(self):
        suite = run_suite(SCENARIOS_DIR)
        self.assertTrue(suite["passed"])
        self.assertGreaterEqual(suite["scenario_count"], 5)
        self.assertEqual(suite["failed_count"], 0)


if __name__ == "__main__":
    unittest.main()
