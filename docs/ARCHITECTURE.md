# Architecture

PTIS v2.0 is split into a deterministic core and external adapters.

## Core Modules

- `bayesian.py`: Maintains vehicle-level destination posteriors. A no-turn observation eliminates the destination located at that junction, then renormalises probability over the remaining reachable destinations.
- `lwr.py`: Propagates two-wheeler density with an LWR finite-volume solver. Unit conversion is explicit: vehicles/minute becomes vehicles/km through `vpm * 60 / kmph`.
- `compliance.py`: Measures target vs observed diversion compliance and returns a command scale for future cycles.
- `decision.py`: Produces capacity-safe smart-link decisions. Expected diversion is capped by receiving capacity after current load and navigation-shadow load.
- `simulation.py`: Runs scenario JSON through the same core used by tests and API, then emits evidence JSON.
- `repository.py`: SQLite event store with salted vehicle hashing. Tests use in-memory SQLite because the local OneDrive sandbox blocks file-backed SQLite.

## External Adapter Boundary

The following are intentionally not hardcoded as fake integrations:

- FASTag/ANPR ingestion
- CCTV/YOLO inference
- Kafka streams
- Redis live cache
- Google Maps / Roads Management data
- BTP signal actuation

Each should be added as an adapter that converts real data into `VehicleObservation`, capacity snapshots, and compliance measurements.

## Decision Cycle

1. Receive checkpoint observation.
2. Update vehicle posterior.
3. Step two-wheeler density model.
4. Update compliance scale from measured turn rate.
5. Estimate destination demand at the current junction.
6. Subtract current load and nav-shadow load from receiving capacity.
7. Activate only when confidence and capacity thresholds are both satisfied.
8. Emit an auditable decision record.
