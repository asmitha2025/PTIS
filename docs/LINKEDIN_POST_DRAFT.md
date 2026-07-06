# LinkedIn Post Draft - Safe Version

I rebuilt PTIS v2.0 from a concept document into a reproducible software proof for capacity-safe traffic diversion decisions.

What is now validated:

- Bayesian destination inference from corridor checkpoint observations.
- Smart-link activation when destination confidence crosses the threshold.
- Capacity-safe diversion logic that refuses to overfill the receiving route.
- Negative cases: low confidence, full receiving capacity, high navigation-shadow load, and mid-route unknown entry.
- A reproducible evidence suite with 26 tests, six scenario cases, a 240-vehicle baseline batch, an 8,000-vehicle synthetic extreme stress test, and OSRM/OpenStreetMap route geometry for the visible road path.
- Official Bengaluru corridor grounding from DULT CMP/CTTP references.
- A real public Bengaluru CCTV evidence audit using the IISc AIM BMD-45 validation sample: 10,194 COCO image records, 106,404 annotations, and five local 1080p sample images checked against metadata.

The important boundary: this is not a field-deployment claim yet. BMD-45 supports vehicle detection/counting evidence, not OD trajectory replay. I am not claiming live BTP/FASTag/Google integration or real-world congestion reduction until a real observed checkpoint dataset and pilot validation are connected.

Repo proof artifacts:

- Scenario suite: `scenarios/`
- Evidence JSON: `evidence/suite_report.json`, `evidence/batch_report.json`, `evidence/extreme_batch_report.json`, `evidence/cctv_bmd45_report.json`
- Proof report: `evidence/PROOF_REPORT.md`
- Validation docs: `docs/VALIDATION.md`
- Public evidence brief: `docs/PUBLIC_EVIDENCE_BRIEF.md`
- Review package: `docs/LINKEDIN_REVIEW_PACKAGE.md`

I would genuinely welcome review from traffic engineers, ITS researchers, and Bengaluru mobility professionals. The question I am testing is narrow and falsifiable:

Can checkpoint no-turn observations infer destination early enough to trigger capacity-safe connector-road diversion before the bottleneck forms?

Current software evidence says yes under the published scenario suite, baseline batch, and 8,000-vehicle synthetic extreme stress test. Real CCTV evidence now supports the detection/counting layer. Field replay with observed checkpoint and OD data is the next gate.