# PTIS Remote Validation Path

This document exists because the project owner may not be physically present in Bengaluru. It defines how PTIS can still be finished for public technical review without making a false field-deployment claim.

## The Honest Constraint

PTIS cannot become "field proven" from software tests, public planning PDFs, or CCTV image datasets alone.

Those sources are still useful:

- Software replay proves the decision engine is reproducible and capacity-safe under the tested scenarios.
- OSRM/OpenStreetMap geometry proves the map route follows a real road-network reference.
- BMD-45 proves real Bengaluru CCTV vehicle-detection evidence can be audited.
- DULT/CMP/CTTP references prove the corridor and junction problem is grounded in official planning material.

They do not prove actual PTIS field impact, travel-time reduction, live police integration, or destination prediction against observed road users.

## Completion Levels

| Level | Name | Status | Allowed Claim |
| --- | --- | --- | --- |
| L1 | Reproducible software validation | Done | PTIS passes deterministic, batch, and 8,000-vehicle stress replay with zero capacity violations. |
| L2 | Public real-world grounding | Done/partial | PTIS is grounded with real route geometry, official Bengaluru planning references, and audited public CCTV detection data. |
| L3 | Remote observed aggregate replay | Next | PTIS was checked against remotely collected aggregate checkpoint counts; no individual destination-accuracy claim. |
| L4 | Field replay with OD labels | Pending | PTIS is field validated only after observed checkpoint, capacity, and ground-truth label CSVs pass the replay gate. |

The project can be made public at L2 now if the wording is strict. L3 can be achieved without travelling to Bengaluru by using a local observer, public-permission video, or an agency/campus collaborator to collect aggregate counts.

## Fastest No-Travel Path

1. Freeze the current public claim at L2.
2. Publish the dashboard as "software validated; field replay pending."
3. Ask one Bengaluru-based observer to collect 30-60 minutes of aggregate counts at one ORR point.
4. Store only aggregate counts. Do not store number plates, faces, raw identity data, or raw vehicle IDs.
5. Run the counts through a remote aggregate replay report.
6. Update PTIS to say "remote observed aggregate replay completed" if the counts pass the safety checks.

This does not replace L4. It gives PTIS a real-world observation layer that can be collected remotely.

## Minimum Remote Observation

One observer can collect:

- Corridor: Marathahalli/ORR toward Whitefield, or Silk Board to Whitefield direction.
- Duration: 30-60 minutes.
- Interval: 60 seconds.
- Checkpoint count: one checkpoint minimum, three checkpoints preferred.
- Vehicle classes: two-wheeler, car, auto, bus, truck/LCV.
- Extra notes: rain, blockage, construction, abnormal queue, police diversion.

Use the template:

```text
data/field_observed/templates/remote_aggregate_counts.csv
```

Run the replay after a real observer CSV is available:

```powershell
$env:PYTHONPATH='backend'
python -m ptis_core.cli run-remote-aggregate scenarios\silk_board_whitefield.json --counts data\field_observed\remote_aggregate_counts.csv --output evidence\remote_aggregate_replay_report.json
```

## Public-Safe Claim After L3

Allowed:

> PTIS is software validated and grounded with public Bengaluru evidence. A remote observed aggregate-count replay was also run to check capacity-safety behavior under measured corridor load. Field OD validation remains pending.

Not allowed:

> PTIS is field proven.

> PTIS reduced congestion by X%.

> PTIS is integrated with BTP, FASTag, Google, or Waze.

> PTIS predicts real destinations accurately in the field.

## Why This Solves The Distance Problem

The project owner does not need to be physically present. The missing piece can be collected remotely by a trusted observer or collaborator, using a small protocol that avoids private data and produces a repeatable CSV.

The professional posture becomes:

> We did not fake field data. We separated software proof, public evidence, remote aggregate observation, and true field OD validation.

That is defensible under technical criticism.