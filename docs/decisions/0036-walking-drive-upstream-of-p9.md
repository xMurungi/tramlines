# 0036 — The walking drive moves upstream of P9: speed becomes the brain's answer

- Status: Accepted (part of the owner-adopted [ADR-0035](0035-proposal-honest-laplaces-demon.md), owner decision 17; neuron choice delegated, by measurement)
- Date: 2026-10-23
- Phase: 5
- Decider: Claude, within the owner's adoption of ADR-0035

## Context
[ADR-0028](0028-senses-and-decoder-chosen.md) stimulated the four P9 neurons (DNp09) as the walking drive *and* read the same four for forward speed. Speed was therefore mostly our own input read back (review in issue #14). ADR-0035 requires that no neuron be both driven and read.

## Survey (`scripts/survey_walking_drive.py`, data `docs/assets/walking_drive_survey.csv`)
P9 receives 11,537 excitatory and 6,776 inhibitory synapses from 1,841 neurons. The strongest excitatory inputs are visual (LC9, LC31); driving those would mean "the fly constantly sees things", not "the fly walks". Eight small central types were stimulated at 100 Hz (1 s, 2 seeds):

| Type (neurons) | P9 | Side effects | Awake neurons |
|---|---|---|---|
| **CB2777 (4)** | **18 Hz** | none | **6,700** |
| PVLP150 (2) | 22 Hz | DNa02 9/21 Hz | 52,600 |
| AVLP369 (2) | 21 Hz | DNa02 12/12 Hz | 27,900 |
| CL270 (8) | 18 Hz | DNa02, GF 5 Hz | 50,200 |
| CB1446 (4) | 15 Hz | **Giant Fiber 41 Hz** (escape) | 30,000 |
| others (PVLP076, CB2659, CB2458) | 10–15 Hz | none | 12,800–42,300 |

Then the dose response of CB2777, alone and paired (2 seeds):

| Drive | 100 Hz | 150 Hz | 200 Hz |
|---|---|---|---|
| CB2777 | P9 18 Hz, 6,700 awake | **P9 28 Hz, 12,400 awake** | P9 37 Hz, 13,000 awake |
| CB2777 + AVLP369 | 38 Hz (GF 4) | 50 Hz (GF 10) | 57 Hz (GF 21) |
| CB2777 + CB2659 | 33 Hz | 46 Hz | 54 Hz, 70,000 awake |

## Options considered
1. **CB2777 at 150 Hz, P9 read only (chosen).** No side effects, graded, and cheap to simulate.
2. **A pair (CB2777 + AVLP369 or + CB2659).** Stronger P9, but more neurons awake, and a little escape-neuron leakage with AVLP369.
3. **Keep driving P9 and read speed from elsewhere.** No literature-anchored alternative speed readout.

## Decision
Option 1. `senses.py`: walking drive = the four CB2777 neurons at 150 Hz. `decoder.py`: forward gain 0.5 mm/s per Hz (P9 ≈ 28 Hz → about 14 mm/s). `tests/test_senses.py` asserts that driven and read neurons never overlap.

## What changed, measured
- **The fly walks straight.** CB2777 drives P9 without exciting the turning neurons (DNa02). The gentle curving walk of ADR-0028 was a side effect of stimulating P9 directly, not the brain steering. In a silent world this brain does not steer; the wall (issue #14, B9) turns it. Result 2 of ADR-0035 (the null brain) will quantify what remains of the brain's contribution.
- **Twice as fast to simulate:** 10 s of the closed loop in 37.5–48.5 s (0.21–0.27× real time, was 0.12×), because far fewer neurons are awake.
- **`DEFAULT_START` moved to (−2, 6) mm** so the straight path crosses the food (presentation, as in ADR-0028). Seed 0, default dish: onto food 1.08 s, feeds, shadow at 6.07 s → jumps off the food. After the jump, feeding lingers 78 ms off the food while MN9 fades from the 50 ms window.
- **Decision points recalibrated** (`scripts/calibrate_decisions.py`): laced food still on edge between 0.70 and 0.80 (3/6 seeds feed), so it stays at **0.72**; the faint shadow's edge moved to 0.05–0.06 (3/6 jump), so it is now **0.055** (was 0.04).
- **Aimed single spikes now split the future more strongly** (decision dish, 16 futures each, 3 s; data `docs/assets/divergence_decision_driven_laced_shadow.csv`):

| Moment | Diverged | Fly jumps (untouched: never) | Fly feeds | Brains fully re-converge |
|---|---|---|---|---|
| On laced food, 1.2 s | 16/16 | **7/16**, two seconds later | 8/16 | 0/16 |
| Shadow growing, 3.35 s | 15/16 | **14/16** | 0/16 | **16/16** |

At the shadow, every brain fires exactly the same spikes as the untouched brain within 0.5 s (correction, 2026-10-24: this was measured on spikes only; whether the full state, voltages included, becomes identical was not checked), yet 14 of 16 flies have escaped, and the escapes fall into only four distinct timings (3.441, 3.442, 3.452, 3.453 s). The brains forget the spike; the bodies do not. Many brain futures, few behaviours.

## Consequences
- Speed now belongs to the brain; the honesty page says so, and that walking itself is still our drive.
- A wall-following, straight-walking fly makes fans whose futures differ mostly in *how far along* the same line they are; in the viewer, divergent turning will matter more than speed.
- Results recorded before this change (ADR-0028 figures, ADR-0029, ADR-0032 tables) describe the earlier drive and stay as history.

## For learners
When you build a body for a brain, check that you are not just hearing your own voice echo back. Here we were pushing four neurons and reading the same four as "speed". Moving the push one step upstream made the speed the brain's own answer, and it showed us something we had missed: left alone, this brain walks straight.
