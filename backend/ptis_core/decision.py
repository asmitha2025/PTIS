from __future__ import annotations

from .models import LinkCapacitySnapshot, LinkDecision, SmartLink


class SmartLinkDecisionEngine:
    """Capacity-safe smart-link activation."""

    def decide(
        self,
        posterior: dict[str, float],
        link: SmartLink,
        capacity: LinkCapacitySnapshot,
        command_scale: float,
    ) -> LinkDecision:
        confidence = float(posterior.get(link.destination_id, 0.0))
        available = max(
            0.0,
            capacity.receiving_capacity_vpm
            - capacity.current_load_vpm
            - capacity.nav_load_vpm,
        )

        if confidence < link.min_confidence:
            return LinkDecision(
                link_id=link.id,
                destination_id=link.destination_id,
                activate=False,
                confidence=confidence,
                available_capacity_vpm=available,
                q_commanded_vpm=0.0,
                q_expected_vpm=0.0,
                reason=f"confidence {confidence:.3f} below threshold {link.min_confidence:.3f}",
            )

        if available <= 0.0:
            return LinkDecision(
                link_id=link.id,
                destination_id=link.destination_id,
                activate=False,
                confidence=confidence,
                available_capacity_vpm=0.0,
                q_commanded_vpm=0.0,
                q_expected_vpm=0.0,
                reason="no receiving capacity after current and navigation load",
            )

        scaled_demand = max(0.0, capacity.demand_vpm) * max(0.0, command_scale)
        expected = min(scaled_demand, available)
        commanded = expected / max(command_scale, 1e-9)
        activate = expected >= link.min_diversion_vpm
        reason = (
            f"P(destination)={confidence:.3f}; "
            f"expected=min(demand {capacity.demand_vpm:.2f} * scale {command_scale:.3f}, "
            f"available {available:.2f}) = {expected:.2f} vpm"
        )
        if not activate:
            reason += f"; below minimum diversion {link.min_diversion_vpm:.2f} vpm"

        return LinkDecision(
            link_id=link.id,
            destination_id=link.destination_id,
            activate=activate,
            confidence=confidence,
            available_capacity_vpm=available,
            q_commanded_vpm=commanded,
            q_expected_vpm=expected,
            reason=reason,
        )
