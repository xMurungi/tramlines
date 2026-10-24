# 0041 — Result 4: the brain forgets, the body remembers, and the body can make the brain remember

- Status: Accepted (delegated; Result 4 of the owner-adopted [ADR-0040](0040-proposal-backward-horizon.md))
- Date: 2026-10-24
- Phase: 5
- Decider: Claude (delegated)

## Context
Laplace's demon knows the past as surely as the future. ADR-0040 asks whether a demon that sees this model's present, to precision ε, can still tell which of two slightly different pasts happened, and for how long. The analysis plan was **pre-registered**: [`docs/science/backward-horizon-plan.md`](../science/backward-horizon-plan.md), merged in PR #23 before the study's code ran on any data.

## Options considered
How to run the pre-registered study:
1. **Exactly as planned**, with every deviation listed (chosen).
2. **Re-plan after the pilot surprises** (the rounding floor; the missed-spike bug). Rejected: re-planning after seeing data is what pre-registration exists to prevent. Surprises go in the deviations and the exploratory section.

## Decision
Ran the plan: 3 seeds × 3 moments (walking 0.5 s, laced food 1.2 s, shadow 3.35 s) × 18 differences (voltage noise 10⁻⁹, 10⁻⁶, 10⁻³, 10⁻¹ mV × 3 draws; one missed spike in transit × 3; one extra spike in a walking-drive neuron × 3). 162 pairs, 159 made (the 3 not made had no spike in transit to miss). Each pair ran 3 s; brains compared every 10 ms with `tramlines.timeline.divergence.brain_difference` (tested). Code: `scripts/backward_horizon_study.py`, `scripts/exact_check.py`, `scripts/analyse_backward_horizon.py`. Data: `docs/assets/backward_horizon.csv`, `backward_horizon_summary.csv`, `exact_check.csv`.

## Deviations from the plan
1. **Exact arithmetic used Python's `decimal` (50 digits), not mpmath.** Same precision; standard library, so no new dependency; much faster.
2. **One pair group was rerun after a bug fix.** The study found that `Brain.inject_spike` accepted a walking-drive neuron that had *already fired at that step*: input neurons have no refractory period, so the check never caught it, and the "extra" spike changed nothing. It happened once (seed 2, walking, draw 0; that pair looked identical after 10 ms). `inject_spike` now refuses such a neuron (test added; determinism gate rerun). The three extra-spike pairs of seed 2 at walking were rerun with the fixed rule, which also shifts which neuron draws 1 and 2 pick (`--replace`, first-run CSV kept outside the repo). No verdict changed (H4 went from 42/66 to 43/67). The earlier free-will study (ADR-0036) was checked: its one non-diverging branch still produced a spike difference, so it was not a no-op.
3. **An exploratory quiet-neuron demonstration** was added to the exact check (below), labelled as such.

## Results against the pre-registered hypotheses
Proportions with Wilson 95% intervals; all seeds (seeds 1–2 alone give the same verdicts).

| | Criterion | Result | Verdict |
|---|---|---|---|
| **H1** the rounding floor | B(10⁻¹³) censored in ≥ 90% of voltage pairs; B(10⁻⁹) ≤ 1 s in ≥ 90% for σ ≤ 10⁻³ | 108/108 [97–100%]; 77/81 [88–98%] | **Supported** |
| **H2** the brain forgets spikes | spike pairs at decisions: B(10⁻⁹) ≤ 3 s in ≥ 50% | 18/36 [34–66%] | **Supported, exactly at the threshold**: the interval spans both sides, so read as "about half" |
| **H3** the body remembers | spike pairs at decisions: body differs in ≥ 50%; voltage σ ≤ 10⁻³: ≤ 25% | 34/36 [82–98%]; 4/81 [2–12%] | **Supported** |
| **H4** the body keeps the brain apart | brain still distinguishable at 3 s more often when the body differs | 43/67 [52–75%] vs **0/92** [0–4%] | **Supported** (intervals do not overlap) |
| **H5** the floor is the computer's | float64 difference stops above 10⁻¹⁴ mV; 50-digit difference below 10⁻²⁰ within 1 s | float64 reached exactly 0; 50 digits 6 × 10⁻³¹ mV | **Not supported as written**; see below |

![Three panels (walking, laced food, shadow) with six kinds of past difference each. Gold dots: when the brain stopped showing the difference to 10⁻⁹ mV; hollow if the body also forgot, filled if the body still shows it; dots at "> 3" never forgot within 3 s. Blue diamonds: Result 1's forward horizon for comparable errors. Voltage differences of 10⁻⁹ to 10⁻³ mV are forgotten within 0.05–0.6 s everywhere, except 10⁻³ mV at the laced food, where four pairs never forget. At the laced food, 0.1 mV, missed spikes and extra spikes are never forgotten and the bodies differ. Under the shadow, the brain forgets 0.1 mV and spike differences within 0.5–2 s although most bodies differ. While walking, missed spikes are forgotten in about 0.5 s, but extra spikes are never forgotten and the bodies differ.](../assets/backward_horizon.png)

**Median B_brain(10⁻⁹)** (bootstrap 95% intervals; "never" = still distinguishable at 3 s):

| Past difference | walking | laced food | shadow |
|---|---|---|---|
| voltage 10⁻⁹ mV | 40 ms (9/9) | 40 ms | 40 ms |
| voltage 10⁻⁶ mV | 170 ms | 170 ms | 170 ms |
| voltage 10⁻³ mV | 310 ms | 360 ms; never in 4/9 | 310 ms |
| voltage 10⁻¹ mV | 420 ms; never in 2/9 | never (9/9) | 1,140 ms [920–1,750]; never in 1/9 |
| one missed spike | 500 ms (6 made) | never (9/9) | 1,080 ms [650–1,260]; never in 1/9 |
| one extra spike | never (9/9) | never in 8/9 | 1,690 ms [1,050–1,830] |

## What the results say
1. **The brain forgets fast.** Small differences in its state fade from the brain within tens to hundreds of milliseconds, at a rate that barely depends on the moment: about 140 ms more for each thousandfold larger difference, which is the 20 ms leak acting on a logarithm.
2. **The body remembers.** When a difference changed what the fly did, its body keeps it: 34 of 36 spike differences at decisions left the flies in different places or states.
3. **The body can make the brain remember.** In every one of 92 pairs whose bodies ended up the same, the brain had forgotten by 3 s. Of 67 pairs whose bodies differed, 43 brains still differed. In this closed loop, a past survives in the brain only by being carried in the body.
4. **Rounding decides what "forgotten" means.** No pair ever became identical bit for bit in the full brain; differences freeze at about 10⁻¹² mV.

![Difference over 1 s on a log scale. Busy test network: float64 falls with the 50-digit curve, then drops to exactly zero at about 370 ms; at 50 digits it keeps falling to 6 × 10⁻³¹ mV. One quiet neuron: float64 freezes at 7.1 × 10⁻¹³ mV from about 170 ms; at 50 digits it keeps falling to 2 × 10⁻³¹ mV.](../assets/exact_check.png)

**H5, explained.** The check's first half held: a scalar re-implementation of the engine matched it bit for bit for 2,000 steps (voltages, inputs and spikes), and in 50-digit arithmetic the difference between two pasts only fades (to 6 × 10⁻³¹ mV in 1 s), never reaching zero. The criterion assumed float64 would *freeze* the difference; on the busy test network it instead *erased* it, reaching exactly zero at 370 ms, because a difference smaller than one rounding step of a voltage far from rest is absorbed outright. A single quiet neuron (exploratory) shows the other side: near rest, the leak's tiny steps round away and the difference freezes at 7.1 × 10⁻¹³ mV for good. The full brain is mostly quiet, hence its floor. So the hypothesis as written is not supported, but its claim stands, more strongly: **in the model, the past only fades; whether the computer erases it or keeps it is decided by rounding, not by the brain.**

## Exploratory (not pre-registered)
- **The body keeps the brain apart only when it changes what the fly senses.** Under the shadow, most altered flies end up in a different place (26 of 27 spike and 0.1 mV pairs), yet their brains forget within 0.5–2 s: most likely because, once the shadow has passed, both flies are near the dish wall away from the food, so their senses receive the same input (likely, not checked pair by pair). At the laced food, the difference is feeding or not, and with it what the fly tastes: those brains never forget.
- **Where the future was hardest to predict (Result 1: laced food), the past is kept longest.** At the laced food both horizons are extreme: the ghost fails within about 0.3 s, and the past is never forgotten. Under the shadow, the future is also hard to predict, but the brain forgets the past. Unpredictability and memory both come from the body's decision; whether the memory reaches back into the brain depends on the senses.

**In one sentence:** this brain erases its past within a second, unless the past moved the body somewhere that feels different.

## Limits
- One model with no learning or memory; it is built to forget. Real brains store memories in their wiring. This says nothing about real flies.
- The principle (dissipative dynamics erase the past) is long known in physics; what is new here is only the concrete measurement in a whole-brain connectome model, pending a literature check.
- 3 seeds, 3 moments, 3 s; "never" means "not within 3 s".
- B is defined on the brain's functional state; the engine's last-spike bookkeeping is ignored by design (plan, Definitions).
- Cost: 75 minutes on 2 workers; memory pressure stayed normal (lowest 72% available).

## Consequences
- Replay mode can show it: two pasts, one present brain, two flies in different places.
- The honesty page states the result and its limits.
- Free-will spikes now refuse neurons that just fired, which also protects the viewer's fan.

## For learners
Ask a brain what happened a second ago, and in this model it often cannot tell you: small differences fade like ripples on a pond. But the fly's body is different. If one past made it eat and the other did not, it stays different, and because it keeps tasting different things, its brain stays different too. We wrote down what we expected before running the experiment, and one of our predictions failed. That failure taught us that the computer itself decides whether the faintest differences vanish or freeze. See [Chapter 22](../book/ch22-the-ghost.md).
