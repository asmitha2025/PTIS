# LinkedIn Reviewer Q&A

Use these answers when a technical reader pushes on PTIS. Keep replies short, calm, and precise.

## How do you know it is the same vehicle?

Best public answer:

> In the current proof, the same-vehicle path is a synthetic anonymized replay trace so the inference logic can be tested against known OD labels. For a real pilot, PTIS would need either privacy-preserving anonymous checkpoint linkage with a measured false-match rate, or an aggregate flow-conservation version using marginal checkpoint counts. We are not claiming live plate, face, GPS, or FASTag tracking.

## Is this just OD estimation?

> It is related to OD estimation, but the project contribution is the operating loop: checkpoint evidence narrows destination belief, then a capacity gate decides whether any connector action is even eligible. Prediction alone is not the claim; prediction plus capacity-safe actuation boundaries is the system.

## What about uninstrumented exits and service roads?

> Correct, checkpoint gaps are a real failure mode. Every unobserved slip road or service road can leak flow out of the corridor. A field pilot must explicitly define checkpoint spacing, known exits, sensor coverage, and uncertainty penalties before making an OD accuracy claim.

## Does BMD-45 prove route prediction?

> No. BMD-45 supports the CCTV vehicle-detection/counting evidence layer. It does not provide multi-checkpoint trajectories or OD labels, so it cannot prove destination prediction. That is why the project separates CCTV audit, software replay, and future field replay.

## What is actually proven today?

> Software behavior: Bayesian update logic, deterministic scenarios, capacity-gate safety, 8,000-vehicle stress replay, synthetic OD calibration in replay, route grounding, and CCTV evidence audit. Field deployment and real destination accuracy are not claimed yet.

## What is the next milestone?

> A shadow pilot or trusted-observer dataset with timestamped checkpoint observations, capacity snapshots, and ground-truth destination labels. That is what converts PTIS from software proof to field validation.
