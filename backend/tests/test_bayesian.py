import json
import unittest
from pathlib import Path

from ptis_core.bayesian import BayesianDestinationEngine
from ptis_core.corridor import Corridor
from ptis_core.models import VehicleObservation


ROOT = Path(__file__).resolve().parents[2]
SCENARIO = ROOT / "scenarios" / "silk_board_whitefield.json"


class BayesianDestinationEngineTest(unittest.TestCase):
    def setUp(self):
        scenario = json.loads(SCENARIO.read_text(encoding="utf-8"))
        self.corridor = Corridor.from_dict(scenario["corridor"])
        self.engine = BayesianDestinationEngine(self.corridor)

    def test_no_turn_observations_renormalise_posterior(self):
        state = self.engine.update(
            VehicleObservation(
                vehicle_id="KA01AB1234",
                entry_junction_id="silk_board",
                junction_id="hsr_layout",
                turned=False,
            )
        )
        self.assertNotIn("hsr_layout", state.posterior)
        self.assertAlmostEqual(state.posterior["whitefield"], 0.24, places=6)

        state = self.engine.update(
            VehicleObservation(
                vehicle_id="KA01AB1234",
                junction_id="sony_world",
                turned=False,
            )
        )
        self.assertAlmostEqual(state.posterior["whitefield"], 0.35294117647058826)

        state = self.engine.update(
            VehicleObservation(
                vehicle_id="KA01AB1234",
                junction_id="marathahalli",
                turned=False,
            )
        )
        self.assertAlmostEqual(state.posterior["whitefield"], 0.6716417910447762)
        self.assertEqual(state.best_destination()[0], "whitefield")

    def test_unknown_entry_gets_reachable_uniform_prior(self):
        state = self.engine.register_vehicle(
            vehicle_id="mid-route",
            entry_junction_id="marathahalli",
            source="unknown",
        )
        self.assertEqual(set(state.posterior), {"marathahalli", "doddanekkundi", "itpl", "whitefield"})
        self.assertAlmostEqual(sum(state.posterior.values()), 1.0)


if __name__ == "__main__":
    unittest.main()
