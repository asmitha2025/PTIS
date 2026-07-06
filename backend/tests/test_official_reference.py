import json
import unittest
from pathlib import Path


class OfficialReferenceExtractTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(Path("data/official_reference_bengaluru_cmp_2020.json").read_text(encoding="utf-8-sig"))

    def test_silk_board_official_count_is_present(self):
        silk_board = next(item for item in self.data["junction_counts"] if item["name"] == "Silk Board Junction")
        self.assertEqual(silk_board["peak_hour_pcu"], 18180)
        self.assertEqual(silk_board["volume_24h_pcu"], 281521)
        self.assertEqual(silk_board["pdf_page"], 80)

    def test_doddanekundi_screenline_is_present(self):
        screenline = next(item for item in self.data["screenline_counts"] if item["id"] == "NSE10")
        self.assertEqual(screenline["both_direction_pcu"], 7823)
        self.assertEqual(screenline["directions"][0]["direction"], "Towards Maratha halli")

    def test_extract_cannot_be_used_as_field_replay(self):
        self.assertEqual(self.data["status"], "official_planning_reference")
        self.assertGreaterEqual(len(self.data["not_field_replay_inputs"]), 3)


if __name__ == "__main__":
    unittest.main()
