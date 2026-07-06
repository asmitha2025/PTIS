# PTIS Remote Observer Packet

Use this when the project owner cannot visit Bengaluru. Send this page to a trusted local observer and ask them to collect aggregate traffic counts only.

## What To Collect

Collect vehicle counts for one checkpoint and one direction.

Preferred location:

- Marathahalli Bridge / ORR toward Whitefield

Alternative locations:

- Kadubeesanahalli toward Marathahalli
- Doddanekkundi toward Whitefield
- Silk Board toward HSR/ORR

## Time Window

Choose one:

- Morning peak: 8:30-10:00 AM
- Evening peak: 5:30-7:30 PM
- Congested incident window if safely observable

Minimum duration: 30 minutes.

Better duration: 60-120 minutes.

## Counting Method

Every 60 seconds, count vehicles crossing the same visual line.

Classes:

- two_wheeler
- car
- auto
- bus
- truck_lcv

Do not record number plates. Do not record faces. Do not publish raw video unless you have permission and privacy review.

## CSV Columns

Use:

```csv
timestamp,checkpoint_id,checkpoint_name,direction,interval_seconds,two_wheeler_count,car_count,auto_count,bus_count,truck_lcv_count,total_count,observer_id,source,weather,notes
```

Example:

```csv
2026-07-03T18:00:00+05:30,marathahalli,Marathahalli Bridge,toward_whitefield,60,92,44,18,6,9,169,remote_obs_01,manual_remote_count,clear,normal queue
```

## Safety Rules

- Stand on a footpath or safe public place.
- Do not stand on the road.
- Do not film private people unnecessarily.
- Do not interact with traffic police unless they ask.
- Stop if the location feels unsafe.

## What This Proves

This proves only aggregate observed flow at a checkpoint during a time window.

It can support:

- measured-load replay
- capacity-safety check
- corridor problem evidence

It cannot support:

- individual destination prediction
- travel-time reduction
- field deployment
- police/FASTag/navigation integration

## Return Files

Return one filled CSV using:

```text
data/field_observed/templates/remote_aggregate_counts.csv
```

Optional:

- one photo of the counting viewpoint
- short note describing exact location and direction