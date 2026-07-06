# arXiv Paper — Structure and Outline
## "Bayesian Destination Inference for Predictive Congestion Prevention in Indian Urban Corridors"
## Target: IEEE Transactions on Intelligent Transportation Systems (IEEE TITS)
## Upload: arXiv.org (cs.AI or eess.SY) — do this FIRST, takes 1 day to appear

---

## HOW TO UPLOAD TO arXiv (do this before applying to any job)

1. Go to arxiv.org → Submit → New Submission
2. Choose category: cs.SY (Systems and Control) primary, cs.AI secondary
3. Upload PDF (LaTeX preferred but PDF accepted)
4. Authors: Asmihari, Asmitha
5. Takes ~1 business day to appear
6. You get a permanent arXiv ID (e.g. arXiv:2026.12345)
7. Add this to your resume immediately

---

## PAPER STRUCTURE (fill in each section — estimated 8-12 pages)

### Abstract (200 words — write this first)
Template:
"Urban traffic management systems in Indian cities face two distinctive challenges absent from Western deployments: (1) two-wheelers constitute 60-65% of the vehicle fleet, behaving as compressible fluid rather than discrete agents, and (2) navigation applications (Google Maps, Waze) with 85%+ penetration route independently, creating secondary congestion on diversion routes. We present PTIS v2.0, a predictive traffic intelligence system for Bengaluru's Outer Ring Road that addresses both challenges. PTIS's core contribution is Bayesian destination inference from junction checkpoint observations: every junction a vehicle passes without turning eliminates destination candidates, building a probability distribution that reaches 65-88% confidence 2-3 junctions before the destination. This confidence triggers smart link activation — dynamic opening of existing connector roads — before congestion forms rather than after. We further contribute: (1) a real-time LWR fluid model (Godunov scheme) for two-wheeler density, (2) a PID closed-loop compliance controller measuring actual vs commanded diversion rates, and (3) a navigation app co-optimisation framework via Google Road Manager API. Simulation on the Silk Board → Whitefield corridor (18km, 6 junctions) shows 43% congestion reduction, 8.2 minutes saved per vehicle, and ₹374 Cr/yr economic benefit. No currently deployed traffic management system in India combines these mechanisms."

---

### 1. Introduction (1-1.5 pages)

1.1 Motivation
- Bengaluru loses ₹37,000 Cr/year to traffic congestion (cite TERI 2018)
- Standard systems: reactive, density-based (SCATS, SITRAFFIC)
- Gap: no predictive destination inference in deployed systems
- India-specific gaps: two-wheeler fleet (62%), nav app conflict, UTC governance

1.2 Contributions
- List all 4 contributions as numbered items
- State novelty clearly: "no prior work combines..."

1.3 Paper Organisation
- One sentence per section

---

### 2. Related Work (1 page)

2.1 Adaptive Signal Control
- SCATS, SCOOT, InSync — reactive, junction-level
- Limitation: no destination inference, no predictive action

2.2 Destination Inference from Probe Data
- FCD (Floating Car Data) based approaches
- Limitation: GPS required, no junction-checkpoint-only approach

2.3 Two-Wheeler Traffic Modelling
- LWR model literature (cite Lighthill & Whitham 1955, Richards 1956)
- Indian urban two-wheeler studies (cite relevant IIT papers)
- Gap: no real-time deployment in traffic management

2.4 Navigation App Interaction with Traffic Control
- Braess paradox in app routing
- Google's internal optimisation — not publicly available
- Gap: no joint public-infrastructure co-optimisation

---

### 3. Problem Formulation (0.5 pages)

- Corridor model: N junctions, M destinations, K vehicle types
- Checkpoint observation: binary (turned / did not turn) per junction
- Goal: P(destination | observations) for each active vehicle
- Action: smart link activation when confidence ≥ θ
- Constraint: capacity-constrained — Qd = min(demand, C − L − Q_nav) × α

---

### 4. Bayesian Destination Engine (1.5 pages)

4.1 Prior Distribution
- Three-tier initialization (FASTag OD matrix, ANPR, max-entropy)
- Derivation of conditional prior P(D | entry_junction)

4.2 Likelihood Model
- P(no-turn at junction j | destination D_i)
- Elimination property: likelihood = 0 for upstream destinations

4.3 Posterior Update Rule
- Full derivation: P(D_i | c_1...c_k) ∝ P(D_i) × ∏ P(no-turn | D_i)
- Normalisation
- Convergence analysis: expected junctions to reach θ confidence

4.4 Mid-Route Joining Vehicles
- Three-tier posterior initialization
- Convergence from high-entropy starting point

---

### 5. Two-Wheeler Fluid Model (1.5 pages)

5.1 LWR Conservation Law
- PDE: ∂ρ/∂t + ∂(ρv(ρ))/∂x = 0
- Greenshields speed-density: v(ρ) = v_free(1 − ρ/ρ_max)
- Parameter calibration: v_free = 48 km/h, ρ_max = 280 tw/km (ORR)

5.2 Godunov Numerical Scheme
- Roe flux at cell interfaces
- CFL stability condition
- 500m spatial discretisation, 30s temporal

5.3 Joint PCU Capacity Estimator
- Effective width reduction: W_eff = W_road × max(0.40, 1 − 0.35 × ρ/ρ_max)
- PCU conversion (IRC 106 standard)
- Integration with Bayesian demand estimation

---

### 6. Closed-Loop Compliance Control (1 page)

6.1 Compliance Measurement
- Entry + exit sensor pair per smart link
- r_actual = q_smartlink / q_upstream (30-second window)

6.2 PID Controller Design
- Error: e(t) = r_actual − r_commanded
- PID law with gains Kp=0.40, Ki=0.12, Kd=0.08
- Ziegler-Nichols tuning methodology (cite Ziegler & Nichols 1942)
- Anti-windup implementation

6.3 Compliance Scaling
- α = clamp(r_actual / r_commanded, 0.50, 1.20)
- Integration into diversion formula

---

### 7. Navigation App Co-Optimisation (1 page)

7.1 The Conflict Problem
- Braess paradox: PTIS diverts to B, Maps routes 400 more to B
- Capacity model: Q_total(B) = Q_PTIS(B) + Q_nav(B)

7.2 Google Road Manager API Integration
- Government registration pathway
- 30-second co-optimisation loop derivation
- Joint capacity constraint enforcement

7.3 Shadow Demand Model
- Q_nav(t+Δ) = β × f(ρ_main(t)) × N_app_estimated
- β = 0.18 calibration methodology
- Apple Maps / unknown apps coverage

---

### 8. Smart Link Activation and Cascade (0.5 pages)

- Activation rule: P(D) ≥ θ AND Qd > minimum_threshold
- Capacity constraint: Qd = min(demand, C − L − Q_nav) × α
- Cascade logic: primary → secondary → tertiary branch roads
- Deactivation hysteresis

---

### 9. Experimental Evaluation (1.5 pages)

9.1 Simulation Setup
- Corridor: Silk Board → Whitefield, 6 junctions, 18km
- Vehicle mix: calibrated from ORR field counts (% by type)
- Demand: FASTag OD matrix (synthetic, NHANES-calibrated)
- Baseline: SCATS adaptive signal control

9.2 Bayesian Model Performance
- Confidence convergence: mean junctions to threshold
- Destination accuracy at activation threshold
- Comparison: FASTag Tier 1 vs ANPR Tier 2 vs unknown Tier 3

9.3 LWR Model Validation
- Density wave propagation vs analytical solution
- CFL stability verification

9.4 System-Level Results
- Congestion reduction: 43% vs SCATS baseline
- Travel time: 8.2 min/vehicle savings
- Compliance sensitivity analysis (α from 0.60 to 1.00)
- Nav app conflict resolution: branch road saturation events eliminated

9.5 Economic Analysis
- Annual benefit: ₹374 Cr/yr (breakdown by component)
- Capex: ₹23.74 Cr
- Sensitivity to key parameters

---

### 10. Discussion (0.5 pages)

- Limitations: static OD matrix (v3.0 will use live OD)
- Deployment requirements: UTC governance framework
- Generalisation: parameter re-calibration for other Indian cities
- Ethical considerations: privacy (checkpoint only, 24hr anonymisation)

---

### 11. Conclusion (0.25 pages)

- Restate three main contributions
- Quantified results
- Future work: multi-corridor, federated learning, live OD

---

### References (target: 20-30 citations)

Key papers to cite:
- Lighthill & Whitham (1955) — LWR model original
- Richards (1956) — LWR model
- Greenshields (1935) — speed-density relationship
- Godunov (1959) — numerical scheme
- SCATS documentation (Roads and Maritime NSW)
- Ziegler & Nichols (1942) — PID tuning
- TERI (2018) — Bengaluru congestion cost
- Recent IEEE TITS papers on Bayesian traffic inference
- Recent papers on two-wheeler traffic India (search IIT Bombay, Madras)
- Google Road Manager API documentation

---

## WRITING TIMELINE

Week 1: Write Sections 1, 3, 4 (Introduction + Bayesian model — you know this deeply)
Week 2: Write Sections 5, 6, 7 (LWR, PID, Nav — directly from PTIS v2.0 doc)
Week 3: Write Sections 2, 8, 9 (Related work, experiments, results)
Week 4: Abstract, Introduction polish, References, format in LaTeX or Word
Week 5: Upload to arXiv → get ID → add to resume → apply to IEEE TITS

Total estimated writing time: 40-60 hours spread over 5 weeks.
Can do this evenings while in a job — does not require full-time commitment.

---

## IMMEDIATE ACTION (before paper is done)

1. Write the abstract (200 words, 2 hours work)
2. Upload even just the abstract + introduction as a preprint
3. Use "arXiv preprint (under review, IEEE TITS)" on resume
4. This is enough — recruiters and engineers will see you took the research seriously
