# LinkedIn Review Package

Last updated: 2026-06-26

Use this package when posting PTIS v2.0 for professional review. The goal is to show real proof without overstating deployment status.

## Screenshot Set

Capture these from `http://127.0.0.1:5173/frontend/?v=real-map-route-1` after running `scripts\verify.ps1`.

1. First viewport: summary, evidence classifier, BMD-45 CCTV frames, and software replay trace.
2. Proof Stack: software, official reference, CCTV and field-replay gate cards.
3. CCTV Evidence: BMD-45 audit metrics and sample images.
4. Field Replay: pending gate with required observed CSV inputs.
5. Proof Report snippet: `evidence/PROOF_REPORT.md` summary.

## Safe Caption

PTIS v2.0 is now a reproducible software proof for capacity-safe smart-link diversion decisions on a Bengaluru ORR corridor scenario. It uses a real OSRM/OpenStreetMap routed road geometry display, is grounded with official Bengaluru mobility planning references, and is audited against a real public Bengaluru CCTV detection dataset sample.

The boundary is important: this is not a field-deployment or congestion-reduction claim yet. BMD-45 supports vehicle detection/counting evidence, not OD trajectory replay. Field replay remains pending until observed checkpoint, capacity and ground-truth data are connected.

## Evidence To Mention

- `26/26` unit/integration tests passed.
- `6/6` published scenarios passed.
- Deterministic `240`-vehicle baseline batch and synthetic `8,000`-vehicle extreme stress passed with `0` capacity violations, `0` overcommands, and `0` false-positive aggregate activations.
- BMD-45 CCTV audit passed with `10,194` metadata rows, `10,194` COCO image records, `106,404` annotations, and `5` local 1080p frames checked.
- DULT/CMP/CTTP references are used as official planning context, not event-level field replay.

## Do Not Say Yet

- Field proven.
- Deployed with BTP, FASTag, ANPR or Google Maps.
- Proven congestion reduction or economic savings.
- Real OD trajectory replay from BMD-45.
- Autonomous traffic-control deployment.

## Reviewer Question

Can checkpoint no-turn observations infer likely destination early enough to trigger a capacity-safe connector-road diversion before a bottleneck forms?

Current answer: yes under the published software scenario suite, deterministic baseline batch, and synthetic 8,000-vehicle extreme stress test. Real CCTV evidence supports the detection/counting layer. Field answer remains pending real checkpoint and OD/ground-truth replay data.

## Suggested Tags And Search Terms

Use role and topic tags rather than claiming endorsement from specific people:

- Intelligent Transportation Systems
- Urban Mobility
- Traffic Engineering
- Bengaluru Mobility
- Smart Cities
- Computer Vision for Traffic
- Bayesian Inference
- Transportation Planning
- Public Sector Innovation
- IISc AIM BMD-45

## Files To Attach Or Link

- `docs/PUBLIC_EVIDENCE_BRIEF.md`
- `docs/LINKEDIN_POST_DRAFT.md`
- `docs/VALIDATION.md`
- `evidence/PROOF_REPORT.md`
- `evidence/cctv_bmd45_report.json`
- `evidence/batch_report.json`