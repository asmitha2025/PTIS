import unittest

from ptis_core.provenance import validate_dataset_manifest


class DatasetProvenanceTest(unittest.TestCase):
    def test_current_manifest_is_valid_but_declared_synthetic(self):
        result = validate_dataset_manifest("data/dataset_manifest.json")
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "synthetic_verification_fixture")
        self.assertIn("dataset_is_synthetic_not_field_data", result["warnings"])

    def test_official_reference_manifest_is_valid_but_not_field_replay(self):
        result = validate_dataset_manifest("data/official_reference_manifest.json")
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "official_planning_reference")
        self.assertIn("dataset_is_official_reference_not_field_replay", result["warnings"])

    def test_bmd45_manifest_is_valid_but_not_field_replay(self):
        result = validate_dataset_manifest("data/bmd45_cctv_manifest.json")
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "public_cctv_detection_dataset")
        self.assertIn("dataset_is_cctv_detection_not_field_replay", result["warnings"])


if __name__ == "__main__":
    unittest.main()
