# Real-World Data Requirements

To move from software proof to field proof, collect and version these inputs.

## Minimum Pilot Dataset

- Junction list, geometry, and turn rules.
- Smart-link inventory with measured receiving capacity.
- Historical OD priors by entry junction and time band.
- Checkpoint observations: vehicle hash, junction, timestamp, source, turned/no-turn.
- Two-wheeler counts or densities per segment at 30-second intervals.
- Upstream approach flow per candidate smart link.
- Current receiving-road load.
- Measured diversion compliance: commanded rate vs actual turn rate.
- Incident/event labels for abnormal days.

## Provenance Rules

- Every dataset needs source, collection window, units, and license/permission.
- Raw identifiers must be hashed before storage.
- Keep scenario fixtures small and public-safe; keep sensitive raw feeds outside Git.
- Every published performance number must map to a reproducible notebook, script, or evidence file.

## Navigation-App Integration Note

Google's public documentation currently refers to Roads Management Insights and Roads Selection APIs, not a generic "Road Manager API". Any production integration must be rewritten against the official product, contract, and access model available to the implementing agency.
