import unittest

from ptis_core.cctv_evidence import validate_cctv_dataset_sample


class CctvEvidenceTest(unittest.TestCase):
    def test_bmd45_sample_validates_as_cctv_evidence_not_field_replay(self):
        report = validate_cctv_dataset_sample()
        self.assertTrue(report["passed"])
        self.assertEqual(report["evidence_type"], "real_public_cctv_detection_dataset")
        self.assertIn("does not provide anonymized vehicle trajectories", report["truth_boundary"])
        self.assertEqual(report["metrics"]["metadata_rows"], report["metrics"]["coco_image_count"])
        self.assertGreater(report["metrics"]["coco_annotation_count"], 100000)
        self.assertGreaterEqual(report["metrics"]["local_image_count"], 5)
        self.assertTrue(all(item["metadata_match"] and item["coco_match"] for item in report["sample_images"]))


if __name__ == "__main__":
    unittest.main()