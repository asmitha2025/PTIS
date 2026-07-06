from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import Destination, Junction, SmartLink


def _normalise(probabilities: dict[str, float]) -> dict[str, float]:
    clean = {key: max(0.0, float(value)) for key, value in probabilities.items()}
    total = sum(clean.values())
    if total <= 1e-12:
        if not clean:
            return {}
        return {key: 1.0 / len(clean) for key in clean}
    return {key: value / total for key, value in clean.items()}


@dataclass(frozen=True)
class Corridor:
    id: str
    name: str
    junctions: dict[str, Junction]
    destinations: dict[str, Destination]
    smart_links: dict[str, SmartLink]
    od_priors: dict[tuple[str, str], dict[str, float]]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Corridor":
        junctions = {
            item["id"]: Junction(
                id=item["id"],
                name=item["name"],
                order=int(item["order"]),
                lat=float(item["lat"]),
                lon=float(item["lon"]),
            )
            for item in data["junctions"]
        }
        destinations = {
            item["id"]: Destination(
                id=item["id"],
                name=item["name"],
                junction_id=item["junction_id"],
            )
            for item in data["destinations"]
        }
        smart_links = {
            item["id"]: SmartLink(
                id=item["id"],
                name=item["name"],
                from_junction_id=item["from_junction_id"],
                to_junction_id=item["to_junction_id"],
                destination_id=item["destination_id"],
                capacity_vpm=float(item["capacity_vpm"]),
                min_confidence=float(item.get("min_confidence", 0.65)),
                min_diversion_vpm=float(item.get("min_diversion_vpm", 0.5)),
            )
            for item in data.get("smart_links", [])
        }
        priors: dict[tuple[str, str], dict[str, float]] = {}
        for item in data.get("od_priors", []):
            source = item.get("source", "fastag")
            entry = item["entry_junction_id"]
            priors[(entry, source)] = _normalise(item["probabilities"])

        return cls(
            id=data["id"],
            name=data["name"],
            junctions=junctions,
            destinations=destinations,
            smart_links=smart_links,
            od_priors=priors,
        )

    def junction_order(self, junction_id: str) -> int:
        try:
            return self.junctions[junction_id].order
        except KeyError as exc:
            raise ValueError(f"Unknown junction_id: {junction_id}") from exc

    def destination_for_junction(self, junction_id: str) -> Destination | None:
        for destination in self.destinations.values():
            if destination.junction_id == junction_id:
                return destination
        return None

    def reachable_destination_ids(self, entry_junction_id: str) -> list[str]:
        entry_order = self.junction_order(entry_junction_id)
        reachable = []
        for destination in self.destinations.values():
            dest_order = self.junction_order(destination.junction_id)
            if dest_order >= entry_order:
                reachable.append(destination.id)
        return reachable

    def prior_for_entry(self, entry_junction_id: str, source: str) -> dict[str, float]:
        reachable = set(self.reachable_destination_ids(entry_junction_id))
        source_key = (entry_junction_id, source)
        fallback_key = (entry_junction_id, "default")
        raw = self.od_priors.get(source_key) or self.od_priors.get(fallback_key)

        if raw is None:
            if not reachable:
                raise ValueError(f"No reachable destinations from {entry_junction_id}")
            return {dest_id: 1.0 / len(reachable) for dest_id in sorted(reachable)}

        filtered = {
            dest_id: probability
            for dest_id, probability in raw.items()
            if dest_id in reachable and dest_id in self.destinations
        }
        if not filtered:
            raise ValueError(
                f"Configured prior for {entry_junction_id}/{source} has no reachable destinations"
            )
        return _normalise(filtered)

    def links_from_junction(self, junction_id: str) -> list[SmartLink]:
        return [
            link
            for link in self.smart_links.values()
            if link.from_junction_id == junction_id
        ]

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "junctions": [vars(j) for j in sorted(self.junctions.values(), key=lambda j: j.order)],
            "destinations": [vars(d) for d in self.destinations.values()],
            "smart_links": [vars(link) for link in self.smart_links.values()],
        }
