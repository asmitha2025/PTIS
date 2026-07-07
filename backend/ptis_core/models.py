from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Junction:
    id: str
    name: str
    order: int
    lat: float
    lon: float


@dataclass(frozen=True)
class Destination:
    id: str
    name: str
    junction_id: str


@dataclass(frozen=True)
class SmartLink:
    id: str
    name: str
    from_junction_id: str
    to_junction_id: str
    destination_id: str
    capacity_vpm: float
    min_confidence: float = 0.65
    min_diversion_vpm: float = 0.5


@dataclass
class VehicleObservation:
    vehicle_id: str
    junction_id: str
    turned: bool = False
    source: str = "anonymous_replay_token"
    entry_junction_id: str | None = None
    timestamp: str = field(default_factory=utc_now_iso)


@dataclass
class VehicleState:
    vehicle_id: str
    entry_junction_id: str
    current_junction_id: str
    posterior: dict[str, float]
    eliminated_destination_ids: set[str] = field(default_factory=set)
    source: str = "anonymous_replay_token"
    last_seen: str = field(default_factory=utc_now_iso)

    def best_destination(self) -> tuple[str, float]:
        if not self.posterior:
            return "unknown", 0.0
        dest_id, confidence = max(self.posterior.items(), key=lambda item: item[1])
        return dest_id, confidence

    def to_public_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["eliminated_destination_ids"] = sorted(self.eliminated_destination_ids)
        return out


@dataclass(frozen=True)
class LinkCapacitySnapshot:
    link_id: str
    demand_vpm: float
    receiving_capacity_vpm: float
    current_load_vpm: float = 0.0
    nav_load_vpm: float = 0.0


@dataclass(frozen=True)
class ComplianceResult:
    target_rate: float
    measured_rate: float
    observed_alpha: float
    command_scale: float
    control_output: float


@dataclass(frozen=True)
class LinkDecision:
    link_id: str
    destination_id: str
    activate: bool
    confidence: float
    available_capacity_vpm: float
    q_commanded_vpm: float
    q_expected_vpm: float
    reason: str


@dataclass(frozen=True)
class CycleAudit:
    cycle: int
    observation: dict[str, Any]
    posterior: dict[str, float]
    best_destination_id: str
    best_confidence: float
    density_tw_per_km: list[float]
    compliance: dict[str, Any]
    decisions: list[dict[str, Any]]


def dataclass_to_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    return value
