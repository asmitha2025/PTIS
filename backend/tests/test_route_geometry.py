from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTE_PATH = ROOT / "data" / "orr_silk_board_whitefield_route_osrm.geojson"


class RouteGeometryReferenceTest(unittest.TestCase):
    def test_osrm_route_geometry_is_real_road_reference_not_field_traffic(self):
        route = json.loads(ROUTE_PATH.read_text(encoding="utf-8-sig"))
        coords = route["features"][0]["geometry"]["coordinates"]

        self.assertEqual(route["status"], "public_osm_routing_reference_not_live_traffic")
        self.assertIn("OpenStreetMap", route["source"])
        self.assertIn("not observed vehicle trajectory", route["truth_boundary"])
        self.assertEqual(route["features"][0]["geometry"]["type"], "LineString")
        self.assertEqual(route["coordinate_count"], len(coords))
        self.assertGreaterEqual(len(coords), 1000)
        self.assertGreater(route["distance_m"], 30000)
        self.assertLess(route["distance_m"], 50000)

        waypoint_ids = [item["id"] for item in route["waypoints"]]
        self.assertEqual(waypoint_ids, [
            "silk_board",
            "hsr_layout",
            "sony_world",
            "marathahalli",
            "doddanekkundi",
            "itpl",
            "whitefield",
        ])

        for lon, lat in coords:
            self.assertTrue(math.isfinite(lon))
            self.assertTrue(math.isfinite(lat))
            self.assertGreater(lon, 77.55)
            self.assertLess(lon, 77.82)
            self.assertGreater(lat, 12.88)
            self.assertLess(lat, 13.04)


if __name__ == "__main__":
    unittest.main()