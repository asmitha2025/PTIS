from __future__ import annotations

from .models import ComplianceResult


def _clip(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


class PIDComplianceController:
    """Closed-loop command scaler for diversion compliance.

    The controller does not pretend drivers obey signs. It measures the gap
    between requested and observed diversion rates, then scales future commands.
    """

    def __init__(
        self,
        kp: float = 0.45,
        ki: float = 0.04,
        kd: float = 0.08,
        integral_limit: float = 4.0,
        output_limit: float = 0.45,
        scale_bounds: tuple[float, float] = (0.55, 1.35),
    ) -> None:
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.integral_limit = integral_limit
        self.output_limit = output_limit
        self.scale_bounds = scale_bounds
        self._integral = 0.0
        self._previous_error = 0.0
        self._scale = 1.0

    @property
    def command_scale(self) -> float:
        return self._scale

    def update(
        self,
        target_rate: float,
        measured_rate: float,
        dt_seconds: float = 30.0,
    ) -> ComplianceResult:
        target = _clip(target_rate, 0.0, 1.0)
        measured = _clip(measured_rate, 0.0, 1.0)
        if target <= 1e-9:
            return ComplianceResult(
                target_rate=target,
                measured_rate=measured,
                observed_alpha=1.0,
                command_scale=self._scale,
                control_output=0.0,
            )

        dt_minutes = max(dt_seconds / 60.0, 1e-6)
        error = target - measured
        self._integral = _clip(
            self._integral + error * dt_minutes,
            -self.integral_limit,
            self.integral_limit,
        )
        derivative = (error - self._previous_error) / dt_minutes
        output = _clip(
            self.kp * error + self.ki * self._integral + self.kd * derivative,
            -self.output_limit,
            self.output_limit,
        )
        self._scale = _clip(1.0 + output, *self.scale_bounds)
        self._previous_error = error
        return ComplianceResult(
            target_rate=target,
            measured_rate=measured,
            observed_alpha=measured / target,
            command_scale=self._scale,
            control_output=output,
        )
