from __future__ import annotations

from dataclasses import dataclass


def _clip(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


class LWRSolver:
    """Finite-volume LWR solver for two-wheeler density.

    Units are explicit:
    - density: two-wheelers / km
    - speed: km / hour
    - flux: two-wheelers / hour
    - inflow_vpm: two-wheelers / minute
    """

    def __init__(
        self,
        n_segments: int,
        dx_km: float = 0.5,
        dt_seconds: float = 30.0,
        v_free_kmph: float = 48.0,
        rho_jam_per_km: float = 280.0,
    ) -> None:
        if n_segments <= 0:
            raise ValueError("n_segments must be positive")
        self.n_segments = n_segments
        self.dx_km = dx_km
        self.dt_hours = dt_seconds / 3600.0
        self.v_free_kmph = v_free_kmph
        self.rho_jam_per_km = rho_jam_per_km
        cfl = v_free_kmph * self.dt_hours / dx_km
        if cfl > 1.0:
            raise ValueError(f"Unstable LWR configuration: CFL={cfl:.3f}")

    def density_from_inflow_vpm(self, inflow_vpm: float) -> float:
        return max(0.0, inflow_vpm) * 60.0 / self.v_free_kmph

    def speed_kmph(self, density: float) -> float:
        rho = _clip(density, 0.0, self.rho_jam_per_km)
        return self.v_free_kmph * (1.0 - rho / self.rho_jam_per_km)

    def flux_vph(self, density: float) -> float:
        rho = _clip(density, 0.0, self.rho_jam_per_km)
        return rho * self.speed_kmph(rho)

    def step(self, density: list[float], upstream_inflow_vpm: float | None = None) -> list[float]:
        if len(density) != self.n_segments:
            raise ValueError(f"Expected {self.n_segments} density segments")

        rho = [_clip(value, 0.0, self.rho_jam_per_km) for value in density]
        left_boundary = (
            self.density_from_inflow_vpm(upstream_inflow_vpm)
            if upstream_inflow_vpm is not None
            else rho[0]
        )
        extended = [left_boundary, *rho, rho[-1]]
        fluxes = []
        for left, right in zip(extended[:-1], extended[1:]):
            fluxes.append(self._interface_flux(left, right))

        updated = []
        for index, value in enumerate(rho):
            next_value = value - (self.dt_hours / self.dx_km) * (
                fluxes[index + 1] - fluxes[index]
            )
            updated.append(_clip(next_value, 0.0, self.rho_jam_per_km))
        return updated

    def effective_width_m(self, density_tw_per_km: float, road_width_m: float) -> float:
        fraction = _clip(density_tw_per_km / self.rho_jam_per_km, 0.0, 1.0)
        return road_width_m * max(0.40, 1.0 - 0.35 * fraction)

    def _interface_flux(self, left_density: float, right_density: float) -> float:
        left_flux = self.flux_vph(left_density)
        right_flux = self.flux_vph(right_density)
        max_wave_speed = self.v_free_kmph
        return 0.5 * (left_flux + right_flux) - 0.5 * max_wave_speed * (
            right_density - left_density
        )


@dataclass(frozen=True)
class JointPCUEstimator:
    road_width_m: float
    lanes: int
    lwr: LWRSolver
    saturation_flow_pcu_per_hour_per_lane: float = 1800.0

    def capacity_vpm(self, density_tw_per_km: float) -> float:
        lane_width = self.road_width_m / self.lanes
        effective_width = self.lwr.effective_width_m(density_tw_per_km, self.road_width_m)
        effective_lanes = min(self.lanes, max(0.0, effective_width / lane_width))
        return self.saturation_flow_pcu_per_hour_per_lane * effective_lanes / 60.0
