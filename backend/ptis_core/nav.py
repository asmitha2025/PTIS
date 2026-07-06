from __future__ import annotations


class NavAppShadowModel:
    """Local estimator for unintegrated navigation-app load.

    This is not a Google integration. It is a transparent capacity reservation
    model used until an official data contract/API feed is available.
    """

    def __init__(self, beta: float = 0.18, app_user_count: float = 1200.0) -> None:
        self.beta = beta
        self.app_user_count = app_user_count

    def predict_vpm(self, main_density_tw_per_km: float, rho_jam_per_km: float) -> float:
        if rho_jam_per_km <= 0:
            raise ValueError("rho_jam_per_km must be positive")
        level = min(max(main_density_tw_per_km / rho_jam_per_km, 0.0), 1.0)
        return self.beta * (level**1.5) * self.app_user_count / 60.0
