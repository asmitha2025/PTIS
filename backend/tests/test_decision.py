import unittest

from ptis_core.decision import SmartLinkDecisionEngine
from ptis_core.models import LinkCapacitySnapshot, SmartLink


class SmartLinkDecisionEngineTest(unittest.TestCase):
    def test_decision_never_exceeds_available_capacity_when_scale_above_one(self):
        link = SmartLink(
            id="sl_test",
            name="test",
            from_junction_id="a",
            to_junction_id="b",
            destination_id="dest",
            capacity_vpm=10.0,
            min_confidence=0.65,
        )
        capacity = LinkCapacitySnapshot(
            link_id="sl_test",
            demand_vpm=100.0,
            receiving_capacity_vpm=10.0,
        )
        decision = SmartLinkDecisionEngine().decide(
            posterior={"dest": 0.99},
            link=link,
            capacity=capacity,
            command_scale=1.35,
        )
        self.assertTrue(decision.activate)
        self.assertLessEqual(decision.q_expected_vpm, decision.available_capacity_vpm)
        self.assertAlmostEqual(decision.q_expected_vpm, 10.0)

    def test_confidence_below_threshold_blocks_activation(self):
        link = SmartLink(
            id="sl_test",
            name="test",
            from_junction_id="a",
            to_junction_id="b",
            destination_id="dest",
            capacity_vpm=10.0,
            min_confidence=0.65,
        )
        capacity = LinkCapacitySnapshot(
            link_id="sl_test",
            demand_vpm=100.0,
            receiving_capacity_vpm=10.0,
        )
        decision = SmartLinkDecisionEngine().decide(
            posterior={"dest": 0.64},
            link=link,
            capacity=capacity,
            command_scale=1.0,
        )
        self.assertFalse(decision.activate)
        self.assertEqual(decision.q_expected_vpm, 0.0)


if __name__ == "__main__":
    unittest.main()
