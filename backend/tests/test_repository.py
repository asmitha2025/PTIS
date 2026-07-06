import unittest
from pathlib import Path

from ptis_core.models import LinkDecision, VehicleObservation
from ptis_core.repository import SQLiteEventStore


class SQLiteEventStoreTest(unittest.TestCase):
    def test_records_observations_and_decisions_without_raw_vehicle_id_column(self):
        store = SQLiteEventStore(":memory:", vehicle_salt="test-salt")
        store.record_observation(
            VehicleObservation(
                vehicle_id="KA01AB1234",
                entry_junction_id="silk_board",
                junction_id="hsr_layout",
                turned=False,
            )
        )
        store.record_decision(
            LinkDecision(
                link_id="sl",
                destination_id="whitefield",
                activate=True,
                confidence=0.70,
                available_capacity_vpm=10.0,
                q_commanded_vpm=9.0,
                q_expected_vpm=9.0,
                reason="test",
            )
        )
        counts = store.counts()
        self.assertEqual(counts, {"observations": 1, "decisions": 1})
        self.assertNotEqual(store.hash_vehicle_id("KA01AB1234"), "KA01AB1234")


if __name__ == "__main__":
    unittest.main()


