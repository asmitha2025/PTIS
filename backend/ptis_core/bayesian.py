from __future__ import annotations

from .corridor import Corridor
from .models import VehicleObservation, VehicleState, utc_now_iso


def _normalise(probabilities: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, value) for value in probabilities.values())
    if total <= 1e-12:
        if not probabilities:
            return {}
        return {key: 1.0 / len(probabilities) for key in probabilities}
    return {key: max(0.0, value) / total for key, value in probabilities.items()}


class BayesianDestinationEngine:
    """Destination inference from binary junction observations.

    The model is intentionally simple and auditable: a no-turn observation at a
    junction eliminates the destination located at that junction. The posterior
    is the prior renormalised over destinations that remain reachable.
    """

    def __init__(self, corridor: Corridor, anpr_epsilon: float = 0.02) -> None:
        self.corridor = corridor
        self.anpr_epsilon = anpr_epsilon
        self._vehicles: dict[str, VehicleState] = {}

    def register_vehicle(
        self,
        vehicle_id: str,
        entry_junction_id: str,
        source: str = "fastag",
    ) -> VehicleState:
        prior = self.corridor.prior_for_entry(entry_junction_id, source)
        if source == "anpr":
            prior = self._smooth(prior, self.anpr_epsilon)

        state = VehicleState(
            vehicle_id=vehicle_id,
            entry_junction_id=entry_junction_id,
            current_junction_id=entry_junction_id,
            posterior=prior,
            source=source,
        )
        self._vehicles[vehicle_id] = state
        return state

    def update(self, observation: VehicleObservation) -> VehicleState:
        entry = observation.entry_junction_id or observation.junction_id
        state = self._vehicles.get(observation.vehicle_id)
        if state is None:
            state = self.register_vehicle(
                vehicle_id=observation.vehicle_id,
                entry_junction_id=entry,
                source=observation.source,
            )

        self.corridor.junction_order(observation.junction_id)
        state.current_junction_id = observation.junction_id
        state.last_seen = observation.timestamp or utc_now_iso()

        destination = self.corridor.destination_for_junction(observation.junction_id)
        if observation.turned:
            if destination is None:
                state.posterior = {}
            else:
                state.posterior = {
                    dest_id: 1.0 if dest_id == destination.id else 0.0
                    for dest_id in state.posterior
                }
        elif destination is not None and destination.id in state.posterior:
            state.eliminated_destination_ids.add(destination.id)
            reduced = {
                dest_id: probability
                for dest_id, probability in state.posterior.items()
                if dest_id != destination.id
            }
            state.posterior = _normalise(reduced)

        return state

    def get_state(self, vehicle_id: str) -> VehicleState | None:
        return self._vehicles.get(vehicle_id)

    def active_states(self) -> list[VehicleState]:
        return list(self._vehicles.values())

    @staticmethod
    def _smooth(probabilities: dict[str, float], epsilon: float) -> dict[str, float]:
        if not probabilities:
            return {}
        n = len(probabilities)
        smoothed = {
            key: value * (1.0 - n * epsilon) + epsilon
            for key, value in probabilities.items()
        }
        return _normalise(smoothed)
