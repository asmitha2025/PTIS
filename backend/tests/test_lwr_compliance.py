import unittest

from ptis_core.compliance import PIDComplianceController
from ptis_core.lwr import JointPCUEstimator, LWRSolver


class LWRAndComplianceTest(unittest.TestCase):
    def test_inflow_density_conversion_uses_minutes_to_hours(self):
        solver = LWRSolver(n_segments=3, v_free_kmph=48.0)
        self.assertAlmostEqual(solver.density_from_inflow_vpm(50.0), 62.5)

    def test_lwr_step_preserves_segment_count_and_bounds(self):
        solver = LWRSolver(n_segments=3, rho_jam_per_km=280.0)
        density = solver.step([88.0, 72.0, 94.0], upstream_inflow_vpm=50.0)
        self.assertEqual(len(density), 3)
        for value in density:
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 280.0)

    def test_pcu_capacity_reduces_as_two_wheeler_density_rises(self):
        solver = LWRSolver(n_segments=3, rho_jam_per_km=280.0)
        estimator = JointPCUEstimator(road_width_m=15.0, lanes=4, lwr=solver)
        low_density_capacity = estimator.capacity_vpm(40.0)
        high_density_capacity = estimator.capacity_vpm(240.0)
        self.assertGreater(low_density_capacity, high_density_capacity)

    def test_pid_scale_increases_when_measured_compliance_is_low(self):
        controller = PIDComplianceController()
        result = controller.update(target_rate=0.80, measured_rate=0.60)
        self.assertGreater(result.command_scale, 1.0)
        self.assertLess(result.observed_alpha, 1.0)


if __name__ == "__main__":
    unittest.main()
