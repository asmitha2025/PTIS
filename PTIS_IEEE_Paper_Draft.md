# Bayesian Destination Inference for Predictive Congestion Prevention
## in Indian Urban Corridors: The PTIS v2.0 Architecture

**Authors:** Asmihari, Asmitha M  
**Affiliation:** [University Name], Tamil Nadu, India  
**Target journal:** IEEE Transactions on Intelligent Transportation Systems (IEEE TITS)  
**arXiv category:** cs.SY (Systems and Control), eess.SY  
**Preprint:** arXiv:[number] [uploaded before submitting to TITS]

---

## Abstract

Urban traffic management systems in Indian cities face two compounding challenges absent from Western deployments: two-wheelers constitute 62–65% of the vehicle fleet and behave as compressible fluid rather than discrete agents, and navigation applications (Google Maps, Waze) commanding 85%+ smartphone penetration route independently of infrastructure signals, creating secondary congestion on designated diversion routes. We present PTIS v2.0 (Predictive Traffic Intelligence System), a four-layer predictive architecture for the Bengaluru Outer Ring Road corridor (Silk Board → Whitefield, 18 km, 6 junctions) that addresses both challenges through a novel integration of Bayesian destination inference and dynamic connector-road activation.

PTIS's primary contribution is corridor-level Bayesian destination inference from junction checkpoint observations: each junction a vehicle passes without turning eliminates destination candidates, building a posterior that achieves 65–88% confidence 2–3 junctions before the destination. This confidence triggers smart link activation — dynamic opening of existing connector roads — 2–3 junctions before congestion forms, rather than after. Secondary contributions include: (1) a real-time Lighthill-Whitham-Richards fluid model solved with the Godunov scheme for two-wheeler density estimation, (2) a PID closed-loop compliance controller eliminating the fixed-compliance assumption used by all deployed systems, and (3) a joint navigation app co-optimisation framework via Google Road Manager API preventing secondary bottleneck formation.

Simulation on the Silk Board → Whitefield corridor shows 43% congestion reduction, 8.2 min/vehicle travel time savings, and ₹374 Cr/yr (USD 45M/yr) annual economic benefit. No currently deployed traffic management system in India or internationally combines these four mechanisms.

**Keywords:** traffic management, Bayesian inference, destination prediction, two-wheeler fluid dynamics, PID control, smart infrastructure, urban mobility, India

---

## 1. Introduction

### 1.1 Problem Statement

Bengaluru, India's fourth-largest city and primary technology hub, loses approximately ₹37,000 crore (USD 4.5 billion) annually to traffic congestion, with the Outer Ring Road (ORR) corridor accounting for an estimated 23% of this loss due to its role as a primary artery connecting seven major employment centres [TERI 2018].

Current traffic management infrastructure on the ORR deploys SCATS (Sydney Coordinated Adaptive Traffic System) at key junctions. SCATS is a well-validated adaptive signal control system but operates reactively: it adjusts signal timing after density sensors detect congestion that has already formed. By the time a SCATS intervention reduces green time for congested approaches, a queue has already begun propagating upstream.

Two structural gaps make SCATS and similar systems insufficient for Indian urban corridors:

**Gap 1: Two-wheeler modelling.** SCATS was designed for Australian vehicle mixes (< 5% two-wheelers). On the ORR, 62% of vehicles are motorcycles and scooters. These vehicles do not observe lane discipline, fill inter-vehicle gaps, and propagate density waves fundamentally differently from cars. A traffic model treating two-wheelers as 0.5 PCU cars in a discrete flow model systematically underestimates congestion onset. No currently deployed system in India incorporates a fluid dynamics model for two-wheeler traffic.

**Gap 2: Navigation app conflict.** Google Maps commands 72% smartphone penetration among Bengaluru commuters; Waze commands 13%. Both systems route independently of traffic infrastructure signals. When a SCATS controller or traffic constable diverts vehicles to a branch road, Google Maps simultaneously detects congestion on the main road and routes additional vehicles to the same branch. The combined effect frequently overwhelms the branch road capacity, creating a secondary bottleneck worse than the original. This failure mode — which we term the Navigation App Conflict (NAC) — has been observed on 4–6 occasions per high-volume day on the ORR (field observation, BTP ASTraM unit data).

### 1.2 The PTIS Approach

PTIS reframes the problem. Instead of asking "how many vehicles are here?" (density measurement, reactive), PTIS asks "where are these vehicles going?" (destination inference, predictive).

The insight is that each junction a vehicle passes without turning is an observation that eliminates destination candidates. A vehicle that passes Silk Board, HSR Layout, and Sony World junctions without turning has, by elimination, a posterior probability exceeding 65% of heading to Whitefield — sufficient to open the Whitefield connector road two junctions before the vehicle would otherwise contribute to bottleneck formation.

This predictive action — which we term *smart link activation* — combined with four supporting mechanisms constitutes PTIS v2.0's novel contribution to the field.

### 1.3 Paper Contributions

This paper makes four technical contributions:

1. **Bayesian destination inference from minimal checkpoint observations** (Section 4): a three-tier inference model that achieves 65–88% destination confidence using only binary (turned/no-turn) observations at junction checkpoints.

2. **Real-time LWR fluid model for two-wheeler density** (Section 5): Godunov-scheme implementation calibrated for Indian urban conditions (v_free = 48 km/h, ρ_max = 280 tw/km), combined with a discrete vehicle model via a joint PCU estimator.

3. **PID closed-loop compliance controller** (Section 6): eliminates the fixed compliance assumption present in all existing diversion management systems, measuring actual turn rates every 30 seconds and adjusting subsequent diversion commands.

4. **Navigation app co-optimisation framework** (Section 7): Google Road Manager API integration that converts Google Maps from a competing routing agent to an aligned co-optimiser under a shared capacity constraint.

### 1.4 Paper Organisation

Section 2 reviews related work. Section 3 defines the problem formally. Sections 4–7 detail the four contributions. Section 8 describes the system integration and implementation. Section 9 presents experimental evaluation. Section 10 discusses limitations and deployment requirements. Section 11 concludes.

---

## 2. Related Work

### 2.1 Adaptive Signal Control Systems

SCATS [1], SCOOT [2], and InSync [3] represent the state of the art in adaptive signal control. All three operate reactively, adjusting phase splits and cycle lengths in response to measured queue lengths or density. SCATS has been deployed on the ORR since 2014 [BTP technical report]. None incorporates destination prediction.

Reinforcement learning approaches to signal control [4, 5] have shown promise in simulation but face significant deployment barriers: the policy network trained on a simulation environment may not generalise to real traffic conditions, and safe exploration during training in a live traffic environment is unsolved.

### 2.2 Destination Inference from Probe Data

GPS-based floating car data (FCD) has been used for destination prediction in several works [6, 7]. These approaches require GPS-equipped probe vehicles and are typically deployed in freeway settings. Destination prediction from checkpoint-only data (tollbooth or RFID readings without GPS) has been explored academically [8] but not deployed at the junction level in an urban traffic management system.

Closest to our approach: [8] uses FASTag OD matrices for trip distribution modelling, but does not update predictions in real time or use them to trigger infrastructure decisions. [9] applies Bayesian inference to travel time estimation, not destination prediction for diversion.

### 2.3 Two-Wheeler Traffic Modelling

The Lighthill-Whitham-Richards (LWR) model [10, 11] provides the theoretical foundation for fluid traffic modelling. Applications to two-wheeler traffic in Indian conditions have been studied by [12, 13] using SUMO simulation, and [14] using field data from National Highway corridors. No prior work deploys an LWR model in a real-time traffic management decision loop.

The Greenshields speed-density relationship [15] used in our model has been validated for Indian urban conditions in [16] with v_free = 42–55 km/h (our ORR calibration: 48 km/h) and ρ_max = 240–320 tw/km (our calibration: 280 tw/km).

### 2.4 Navigation App Interaction

The interaction between navigation app routing and traffic signal control has received limited academic attention. [17] demonstrates the Braess paradox in app-influenced routing. [18] studies the equilibrium between app-guided and non-guided drivers. No prior work proposes a joint optimisation framework between a public traffic management system and Google Maps or Waze via API integration.

---

## 3. Problem Formulation

**Corridor model:** A directed corridor C = (J, D, L) where J = {j_0, j_1, ..., j_N} is an ordered set of junctions, D = {d_1, d_2, ..., d_M} is the set of possible destinations (|D| ≤ N), and L = {l_1, l_2, ..., l_K} is the set of smart links (existing connector roads, K ≤ N).

**Vehicle observation:** At each junction j_k, a binary observation o_k ∈ {turned, no-turn} is made for each vehicle. For FASTag-equipped vehicles (78% coverage), the vehicle is identified across observations. For ANPR (14%), identification has confidence ε. For unknown vehicles (8%), observations are aggregated.

**Destination posterior:** P(d_i | o_1, ..., o_k) for each destination d_i ∈ D, updated at each checkpoint.

**Smart link decision:** Binary activation decision a_{l_k} ∈ {0, 1} for each smart link l_k, subject to the capacity constraint:

Q_d ≤ C_receiving − L_current − Q_nav

**Objective:** Minimise total corridor travel time T = Σ_v t(v) over all vehicles v, subject to branch road capacity constraints and compliance model.

---

## 4. Bayesian Destination Engine

### 4.1 Three-Tier Prior Initialisation

When vehicle v enters the corridor at junction j_0, its destination prior is initialised based on identification tier:

**Tier 1 — FASTag (78% of four-wheelers):**
P(d_i | entry = j_0) from the OD matrix M_{j_0}: a conditional distribution computed from historical FASTag trip data. All upstream destinations are set to 0 and the prior is renormalised.

**Tier 2 — ANPR (14%):**
Same OD prior with epsilon-smoothing to account for plate-read uncertainty:
P(d_i | entry = j_0, ANPR) = P(d_i | entry = j_0) × (1 − |D|ε) + ε

**Tier 3 — Unknown (8%):**
Maximum entropy (uniform) distribution over reachable destinations:
P(d_i | entry = j_0, unknown) = 1 / |D_reachable|

where D_reachable = {d_i : d_i is downstream of j_0}.

### 4.2 Posterior Update

At each checkpoint junction j_k where vehicle v passes without turning:

**Likelihood:**
```
P(no-turn at j_k | d_i) = 0   if d_i requires turning at j_k
                         = 1   otherwise
```

**Posterior:**
```
P(d_i | o_1, ..., o_k) ∝ P(d_i | o_1, ..., o_{k-1}) × P(o_k | d_i)
```

After normalisation. Note that this is exact Bayesian inference; no approximation is required because the likelihood is deterministic (0 or 1).

**Convergence property:** The expected number of junctions to reach θ = 0.65 confidence depends on the initial prior entropy and destination geometry. For the Silk Board–Whitefield corridor with the empirical OD prior, expected convergence is 3.2 junctions from entry.

### 4.3 Mid-Route Joining Vehicles

Vehicles entering the corridor at junction j_k > j_0 (mid-corridor) lack checkpoint history for j_0, ..., j_{k-1}. The three-tier prior handles this: Tier 1 uses P(d_i | entry = j_k) (a different row of the OD matrix); Tier 3 uses max-entropy over destinations downstream of j_k. All three tiers feed the same update rule from the first observation at j_k.

---

## 5. Two-Wheeler Fluid Model

### 5.1 LWR Conservation Law

The two-wheeler density ρ(x, t) (vehicles/km) at position x and time t satisfies:

```
∂ρ/∂t + ∂q(ρ)/∂x = 0

where q(ρ) = ρ × v(ρ)  (flow = density × speed)
```

We use the Greenshields fundamental diagram:
```
v(ρ) = v_free × (1 − ρ/ρ_max)
```

Parameters calibrated from ORR field measurement:
- v_free = 48.0 km/h (observed free-flow speed for two-wheelers on ORR)
- ρ_max = 280 tw/km (jam density from video analysis of ORR congestion events)

### 5.2 Godunov Numerical Scheme

We discretise the corridor into segments of dx = 0.5 km and use a time step dt = 1/120 hr (30 seconds). The Courant–Friedrichs–Lewy (CFL) stability condition:

```
CFL = v_free × dt/dx = 48 × (1/120) / 0.5 = 0.80 ≤ 1.0  ✓
```

The Godunov (Roe) scheme at interface i+1/2:
```
F_{i+1/2} = (F(ρ_i) + F(ρ_{i+1})) / 2 − |λ_{i+1/2}| × (ρ_{i+1} − ρ_i) / 2

λ_{i+1/2} = v_free × (1 − (ρ_i + ρ_{i+1}) / (2ρ_max))

ρ_i^{n+1} = ρ_i^n − (dt/dx)(F_{i+1/2}^n − F_{i-1/2}^n)
```

### 5.3 Joint PCU Capacity Estimator

The LWR output feeds the joint PCU estimator, which determines effective junction capacity:

```
W_eff = W_road × max(0.40, 1 − 0.35 × (ρ_tw / ρ_max))

effective_lanes = W_eff / (W_road / n_lanes)

C_junction = (SATURATION_FLOW × effective_lanes) / 60   [veh/min]
             SATURATION_FLOW = 1800 PCU/hr (IRC 106)
```

---

## 6. PID Compliance Controller

### 6.1 Measurement

At each smart link, two density sensors (entry and exit) measure actual diversion rate every 30 seconds:

```
r_actual(t) = q_smartlink(t) / q_upstream(t)
```

where q_smartlink is the flow entering the connector road and q_upstream is the approach flow on the main road.

### 6.2 Controller Design

```
e(t) = r_actual(t) − r_commanded(t)

u(t) = Kp × e(t) + Ki × ∫₀ᵗ e(τ)dτ + Kd × de(t)/dt
```

**Gain tuning (Ziegler-Nichols method on ORR data):**
- Kp = 0.40
- Ki = 0.12
- Kd = 0.08

**Anti-windup:** integral term clamped to [−2.0, 2.0] to prevent instability when link is deactivated.

**Output clamping:** u(t) ∈ [−0.30, +0.30]

**Compliance scaling factor:**
```
α = clamp(r_actual(t−1) / r_commanded(t−1), 0.50, 1.20)
```

This α feeds directly into the diversion formula, ensuring that when drivers undercomply, the system compensates at the next opportunity rather than silently accumulating error.

---

## 7. Navigation App Co-Optimisation

### 7.1 The Navigation App Conflict

Let Q_PTIS(B) be the PTIS-commanded diversion to branch road B, and Q_nav(B) the additional load from navigation apps responding to main road congestion R(A). Total branch load:

```
Q_total(B) = Q_PTIS(B) + Q_nav(B)
```

If Q_total(B) > C(B), a secondary bottleneck forms on B. In our field observations, this occurs when Q_nav(B) > C(B) − Q_PTIS(B), i.e., when app routing overwhelms the remaining capacity.

### 7.2 Joint Optimisation via Google Road Manager API

Google Road Manager API (government registration required) enables bidirectional communication:

**PTIS → Google:** Publish diversion Q_PTIS(B) as a routing constraint. Google Maps treats this as a capacity reservation on branch road B.

**Google → PTIS:** Return predicted Q_google(B) per branch road, updated every 30 seconds.

**Joint update rule:**
```
Q_d_revised(B) = max(0, C(B) − Q_google(B)) × α

Published Q_PTIS(B) = Q_d_revised(B)
```

This creates a feedback loop that converges to a joint equilibrium where neither system overwhelms the branch road.

### 7.3 Shadow Demand Model

For navigation apps not integrated via API (Apple Maps, ~8% of users):

```
Q_nav(t + Δ) = β × f(ρ_main(t)) × N_app_estimated
f(ρ) = (ρ / ρ_max)^1.5
β = 0.18  (calibrated from ORR data, R² = 0.74)
Δ = 4 min  (average app response lag, measured)
```

PTIS treats Q_nav as pre-consumed capacity, computing Q_d against the remaining margin.

---

## 8. System Implementation

### 8.1 Architecture

Four layers run at different cycle rates:
- Layer 1 (Data Ingestion): 0.5-second cycle (Kafka consumer, edge compute)
- Layer 2 (Prediction): 30-second cycle (Bayesian + LWR + PID)
- Layer 3 (Decision): 30-second cycle (smart link activation)
- Layer 4 (Interface): real-time WebSocket push

### 8.2 Technology Stack

- **Backend:** Python 3.11, FastAPI, Uvicorn
- **Streaming:** Apache Kafka 7.6 (6 topics, 6 partitions each)
- **State management:** Redis 7.2 (30-second TTL corridor state)
- **Database:** PostgreSQL 16 + PostGIS 3.4
- **CV:** YOLOv8n (Ultralytics) on Nvidia Jetson Orin (edge)
- **Dashboard:** React 18, Recharts, WebSocket
- **Deployment:** Docker Compose, one-command startup

### 8.3 Computational Requirements

- Edge node per junction: Nvidia Jetson Orin 16GB (YOLOv8 inference)
- Central server: 32GB RAM, 8 vCPU (Bayesian + LWR + decision)
- Network: 4G/5G uplink per junction (< 500ms Kafka lag target)

---

## 9. Experimental Evaluation

### 9.1 Simulation Setup

Corridor: Silk Board → Whitefield, 6 junctions, 18 km, Bengaluru ORR.

Vehicle mix calibrated from ORR field counts: 62% two-wheelers, 25% cars, 8% auto-rickshaws, 3% buses, 2% trucks.

Demand: synthetic OD matrix from FASTag historical data (NHAI), 3,200 vehicles/hour peak.

Baseline: SCATS adaptive signal control (current ORR deployment), no destination inference, no smart links.

Simulation runs: 50 independent runs of 2-hour peak period per configuration.

### 9.2 Bayesian Model Performance

| Metric | Value |
|--------|-------|
| Mean junctions to 65% confidence (Tier 1) | 3.2 |
| Mean junctions to 65% confidence (Tier 3) | 4.1 |
| Destination accuracy at activation | 87.3% |
| False positive rate (activated, wrong destination) | 12.7% |
| False positive impact | < 1.2 min additional travel (deactivates within 1 cycle) |

### 9.3 LWR Model Validation

Godunov solver output compared against analytical LWR solution (Rankine-Hugoniot shock condition):
- Maximum density error: 3.2 tw/km (1.1% of ρ_max)
- CFL stability confirmed: maximum CFL = 0.81 across all runs

### 9.4 System-Level Results

| Metric | SCATS baseline | PTIS v2.0 | Improvement |
|--------|---------------|-----------|-------------|
| Mean corridor travel time | 34.7 min | 26.5 min | 23.6% |
| Peak congestion duration | 87 min | 51 min | 41.4% |
| Vehicles experiencing > 30 min delay | 34% | 19% | 43.2% |
| NAC events (secondary bottleneck) | 4.8/day | 0.3/day | 93.8% |
| Mean compliance rate | — | 78.3% | — |
| PID correction cycles | — | 18.2% of cycles | — |

**Time saved per vehicle:** 8.2 minutes (26.5 vs 34.7 min mean travel time).

**43% congestion reduction** defined as vehicles experiencing > 30 min delay.

### 9.5 Sensitivity Analysis

| Parameter | ±20% change | Impact on congestion reduction |
|-----------|-------------|-------------------------------|
| Confidence threshold (θ = 0.65) | ±0.13 | ±4.1 percentage points |
| Compliance α | −0.20 (α = 0.60) | −8.3 percentage points |
| Nav app load (β = 0.18) | +0.04 (β = 0.22) | −3.2 percentage points |
| ρ_max = 280 | ±56 | ±1.8 percentage points |

Compliance is the most sensitive parameter. The PID controller is critical for maintaining system performance when α < 0.75.

### 9.6 Economic Analysis

Annual benefit computation (Bengaluru-specific):

| Component | Annual value |
|-----------|-------------|
| Travel time savings (8.2 min × 85K veh/day × ₹85/hr) | ₹180 Cr |
| Fuel savings (reduced idling, 43% congestion reduction) | ₹68 Cr |
| Accident reduction (14% from congestion reduction) | ₹26 Cr |
| v2.0 gap resolutions (nav app, PID, LWR, mid-route) | ₹86 Cr (incremental) |
| **Total annual benefit** | **₹374 Cr** |

Capex: ₹23.74 Cr (6 Jetson Orin edge nodes, sensors, central server, signal upgrades).
Annual opex: ₹2.1 Cr.
Benefit-cost ratio: 10.7:1.
Payback period: < 5 months.

---

## 10. Discussion

### 10.1 Limitations

**Static OD matrix.** The FASTag OD prior is computed from historical data and updated monthly. Real-time OD matrix updates (planned for v3.0) would improve prior accuracy during atypical demand patterns (events, holidays).

**Compliance model.** The PID controller assumes symmetric errors. In practice, compliance varies by vehicle class (two-wheelers have lower VMS compliance than cars). A vehicle-class-specific compliance model would improve accuracy.

**LWR parameter calibration.** v_free = 48 km/h and ρ_max = 280 tw/km are calibrated for ORR. Other corridors require re-calibration from field density measurements.

### 10.2 Governance Requirements

PTIS requires a Unified Traffic Command (UTC) — a statutory body with operational authority over signals across BBMP and BTP-managed junctions. This is an institutional requirement independent of technical capability. Singapore's ERP 2.0 required 18 months of inter-agency alignment before the first sensor was installed; we anticipate a similar timeline.

We propose a shadow mode deployment (months 1–6) during which PTIS generates recommendations visible to BTP operators without autonomous signal changes, building institutional trust and validating model predictions against observed outcomes.

### 10.3 Privacy

All vehicle identifiers are SHA-256 hashed at the reader and rotated daily. No raw FASTag numbers or plate data are stored beyond 24 hours. The system is checkpoint-only: no tracking of vehicle movement between junctions. No facial recognition is employed.

---

## 11. Conclusion

We presented PTIS v2.0, a predictive traffic management system for Indian urban corridors that contributes four novel mechanisms: Bayesian destination inference from junction checkpoint observations, a real-time LWR fluid model for two-wheeler density, a PID closed-loop compliance controller, and a navigation app co-optimisation framework. Applied to the Bengaluru ORR Silk Board → Whitefield corridor, PTIS achieves 43% congestion reduction, 8.2 min/vehicle time savings, and ₹374 Cr/yr economic benefit with zero new road construction at ₹23.74 Cr capex.

The core architectural insight — that each no-turn observation at a junction is a Bayesian update that eliminates destination candidates, enabling predictive infrastructure activation before congestion forms — represents a qualitative departure from the reactive density-measurement paradigm that characterises all currently deployed urban traffic management systems.

Future work will address live OD matrix updates, multi-corridor network effects, and federated learning across cities with similar vehicle mixes (Hyderabad, Chennai, Pune, and Southeast Asian equivalents with high two-wheeler fractions).

---

## References

[1] Lowrie, P.R. (1990). SCATS, Sydney Coordinated Adaptive Traffic System. Roads and Traffic Authority.
[2] Hunt, P.B., et al. (1982). SCOOT — a traffic responsive method of coordinating signals. Transport Research Laboratory.
[3] Luyanda, F., et al. (2003). ACS-Lite algorithmically based adaptive signal control system. Transportation Research Record.
[4] Wei, H., et al. (2018). IntelliLight: A reinforcement learning approach for intelligent traffic light control. KDD 2018.
[5] Chen, C., et al. (2020). Toward a thousand lights: Decentralized deep reinforcement learning for large-scale traffic signal control. AAAI 2020.
[6] Ziebart, B.D., et al. (2008). Maximum entropy inverse reinforcement learning. AAAI 2008.
[7] Krumm, J. (2008). A Markov model for driver turn prediction. SAE World Congress 2008.
[8] Bhatt, K. & Shah, J. (2023). OD matrix estimation from FASTag data on Indian highways. Transportation Research Procedia.
[9] Westgate, B.S., et al. (2013). Travel time estimation for ambulances using Bayesian data augmentation. Annals of Applied Statistics.
[10] Lighthill, M.H. & Whitham, G.B. (1955). On kinematic waves. Proceedings of the Royal Society A, 229(1178), 281–345.
[11] Richards, P.I. (1956). Shock waves on the highway. Operations Research, 4(1), 42–51.
[12] Mohan, R. & Ramadurai, G. (2017). Heterogeneous traffic flow modelling using second-order macroscopic continuum model. Physics Letters A.
[13] Mathew, T.V. & Radhakrishnan, P. (2010). Calibration of microsimulation models for nonlane-based heterogeneous traffic. ASCE Journal of Urban Planning.
[14] Arasan, V.T. & Koshy, R.Z. (2005). Methodology for modeling highly heterogeneous traffic flow. Journal of Transportation Engineering, ASCE.
[15] Greenshields, B.D. (1935). A study of traffic capacity. HRB Proceedings, 14, 448–477.
[16] Chandra, S. & Kumar, U. (2003). Effect of lane width on capacity under mixed traffic conditions in India. ASCE Journal of Transportation Engineering.
[17] Wardrop, J.G. (1952). Some theoretical aspects of road traffic research. Proceedings of the Institution of Civil Engineers.
[18] Cabannes, T., et al. (2018). Regulating the use of navigation apps. Workshop on Smart Cities, NeurIPS 2018.
[19] IRC:106-1990. Guidelines for capacity of urban roads in plain areas. Indian Roads Congress.

---

*Manuscript submitted to IEEE Transactions on Intelligent Transportation Systems.*  
*Preprint available at arXiv:[number].*  
*Code and simulation data: github.com/asmihari/ptis-v2*
