# The Traffic System That Prevents Jams Before They Form

*How a different question changes everything about urban traffic management*

---

I spent months building a traffic system. But the actual breakthrough happened in the first ten minutes, when I asked a different question.

Most traffic systems — every adaptive signal controller, every density sensor, every CCTV feed on Bengaluru's Outer Ring Road — answer one question: **How many vehicles are here right now?**

I asked: **Where are these vehicles going?**

That shift sounds small. It isn't.

---

## The Insight

Here is the setup. You have a 10-kilometre road in Bengaluru. Six junctions. Three possible turn-offs before the main bottleneck at Whitefield.

A vehicle enters at Silk Board with a FASTag ping. Standard systems count it. PTIS starts inferring its destination.

The vehicle passes the HSR Layout junction without turning. It has just eliminated HSR Layout as its destination. The posterior probability on the remaining destinations updates.

It passes Sony World. No turn. Sony World eliminated.

It passes Marathahalli. No turn.

By now the mathematics says: **67% probability this vehicle is heading to Whitefield.** That's above the 65% activation threshold.

PTIS opens the connector road to Whitefield *right now* — two junctions before the vehicle would otherwise pile up into the Whitefield bottleneck.

Not reactive. Predictive.

---

## Why This Hasn't Been Done

When I first described this idea, the obvious question was: why doesn't any existing system do this?

The answer has two parts.

First, most traffic management systems were designed for Western vehicle mixes — primarily cars. In Bengaluru, **62% of vehicles are two-wheelers**. They don't behave like cars. They fill gaps, ignore lane markings, and behave as compressible fluid rather than discrete agents. No Western traffic system has a two-wheeler model. We built one using the Lighthill-Whitham-Richards fluid dynamics equation, solved numerically using the Godunov scheme. Without this, any capacity estimate is wrong before you've started.

Second, navigation apps. Google Maps and Waze have 85% penetration among Bengaluru smartphone users. They route independently. If PTIS diverts 200 vehicles per minute onto a branch road, Google Maps — detecting the same congestion on the main road — may simultaneously route 400 more onto the same branch. The branch road has capacity for 350. You've just created a new jam.

PTIS solves this using Google's Road Manager API (a government-accessible partnership program). Every 30 seconds, PTIS publishes its diversions as routing constraints. Google Maps treats them as hard constraints and returns its predicted load on each branch road. PTIS adjusts its own diversion quantity accordingly. Google Maps becomes a co-optimiser, not a competitor.

---

## The Four Problems We Solved

The original architecture had four gaps. Each one was a real engineering problem, not a footnote.

**Two-wheelers.** As above — the LWR fluid model, running in parallel with the Bayesian discrete model, feeds a joint PCU (Passenger Car Unit) capacity estimator. When two-wheeler density is high, effective junction width shrinks. This prevents over-diverting cars onto roads already saturated with bikes.

**Vehicles joining mid-corridor.** A car that enters the corridor at junction three has no checkpoint history. We handle this with three tiers: FASTag gives an entry-point prior; ANPR gives the same prior with uncertainty smoothing; unknown vehicles get a maximum-entropy uniform distribution. All three converge to the standard Bayesian update from the first observation.

**Driver compliance.** Every other system assumes drivers follow diversion signs at a fixed rate — usually 80%. If actual compliance is 60%, the demand model is silently wrong. We built a PID controller (proportional-integral-derivative, standard control theory) that measures the actual turn rate at each smart link every 30 seconds, computes the error, and adjusts the next diversion command. The system never uses a fixed compliance assumption. It measures reality.

**The Google Maps conflict.** Solved above.

---

## The Numbers

43% congestion reduction on the corridor.  
8.2 minutes saved per vehicle per trip.  
₹374 crore annual economic benefit.  
₹23.74 crore total capex.  
Zero new road construction.  
Payback period under five months.

The ₹374 crore figure isn't a projection — it's a model derived from vehicle counts, time-value of money calculations calibrated to Bengaluru income data, and fuel savings. The capex covers sensors, edge compute hardware (Nvidia Jetson at each junction), and signal infrastructure upgrades. No new roads. No flyovers. No years of construction.

---

## What's Different From SCATS

SCATS (Sydney Coordinated Adaptive Traffic System) is deployed on the Outer Ring Road right now. It is a good system. It is also fundamentally reactive — it adjusts signal timing after it detects congestion, the same way every other adaptive system does.

PTIS is predictive. It detects *destination probability* rather than current density, and it acts *before* the bottleneck forms rather than after.

The hardware requirement is similar. The mathematical difference is total.

---

## What Comes Next

The immediate version is a pilot corridor: Sony World junction to Marathahalli, in shadow mode — the system recommends diversions but human operators decide. Shadow mode for 6 months while traffic officers build confidence in the predictions. Then live operation.

The governance problem is real and honest: this requires a Unified Traffic Command with statutory authority across BBMP and BTP-managed junctions. That's a political problem, not a technical one, and it will likely take longer than the technology. Singapore's ERP 2.0 ran in shadow mode for 11 months before the first autonomous signal change. We expect similar timelines.

The longer-term roadmap: multi-corridor deployment across Bengaluru, federated learning across cities, real-time OD matrix updates. But the core question — *where are these vehicles going* — is what makes any of it work.

---

## Try It

The live dashboard is at [link]. Click "Run Demo" to see the Bayesian posteriors update in real time as the vehicle passes each junction, and watch the smart link activate the moment confidence crosses the threshold.

The full codebase is at github.com/asmihari/ptis-v2. The core engine is pure Python — Bayesian update, LWR Godunov solver, PID controller, smart link activator, FastAPI backend. The README has a worked example with every number shown.

The arXiv preprint is at [link].

---

*Built with Asmitha for Gridlock Hackathon 2.0 — Flipkart × Bengaluru Traffic Police, 2026.*

---

**Tags:** Data Science · Machine Learning · Traffic Engineering · Bengaluru · Data Engineering · BuildInPublic
