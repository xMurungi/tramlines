# 0037 — Result 1, first pass: to foresee this brain you need its spikes, not its decimals

- Status: Accepted (delegated; Result 1 of the owner-adopted [ADR-0035](0035-proposal-honest-laplaces-demon.md))
- Date: 2026-10-23
- Phase: 5
- Decider: Claude (delegated)

> **Second pass:** [ADR-0038](0038-result-1-second-pass.md) repeats this on 3 seeds with 3 draws each. Finding 1 below does not hold at the laced food, where even 0.001 mV fails about half the time. Finding 3's walking case is void: no spike was in transit (correction, 2026-10-24).

## Context
ADR-0035 asks how much you must know about a brain to predict it. The perfect ghost (a bit-exact copy) is the control and is always right. Here the ghost is given *imperfect* knowledge of the brain at a chosen moment, and we measure how long its predicted path stays right.

## Method
- `tramlines/timeline/perturb.py`: four ways a measurement of the brain could fall short. Each draws from its own generator, never the brain's, so the ghost's future sensory input is the same as the truth's:
  - **voltage:** every voltage known only to within Gaussian noise of σ mV;
  - **float32:** the whole state stored at single precision;
  - **one in-flight spike missed**;
  - **partial:** only a fraction of neurons observed, the unseen ones assumed at rest.
- `scripts/horizon_study.py`: seed 0, decision dish, three moments (walking at 0.5 s, on laced food at 1.2 s, the faint shadow at 3.35 s); truth and ghosts run 3 s ahead. "Stays right" = the paths stay within 0.1 mm. Data `docs/assets/horizon.csv`.

![Three panels (walking, laced food, shadow). Bars show how long the ghost's path stays right. The control, voltage errors up to 0.001 mV, float32 and 99.9% observation stay right for all 3 s everywhere. Voltage errors of 0.1 to 1 mV, one missed spike at the decision points, and 99% or less observation fail within 42 to 387 ms.](../assets/horizon.png)

## Findings (first pass)
1. **Continuous error barely matters.** Voltages known to within 10⁻¹² … 10⁻³ mV, or the whole state in float32: the ghost's path is right for all 3 s at every moment. At 0.001 mV on the laced food some spikes differ at once, yet the behaviour never does. Errors this small decay; this model is stable, not chaotic.
2. **The edge for continuous error sits between 0.01 and 0.1 mV.** At 0.01 mV the ghost still walks right (except on laced food: 361 ms); at 0.1–1 mV it is wrong within 46–359 ms, predicting jumps and meals that never happen.
3. **A single missed spike is decisive at decision points and harmless elsewhere.** Missing one spike in transit: ~~right for all 3 s while walking~~ (**correction, 2026-10-24:** at that moment of seed 0 no spike was in transit, so this ghost was a perfect copy and the walking result is void; [ADR-0038](0038-result-1-second-pass.md) has the corrected count from other seeds), wrong within **242 ms** on laced food and **52 ms** under the shadow (it predicts an escape that never comes).
4. **You must see almost everything.** Observing 99.9% of neurons (about 140 unseen): right for all 3 s. Observing 99% (about 1,400 unseen): wrong within 52–387 ms everywhere.

**In one sentence:** to foresee this brain you need to know nearly every neuron and every spike in flight; you do not need its voltages to more than about a hundredth of a millivolt.

## Limits of this first pass
- One seed and one random draw per kind of error: these are single measurements, not distributions. The next pass needs several seeds, several draws and more moments.
- "Partial" assumes unseen neurons are at rest. A smarter ghost (guessing from neighbours) might do better.
- The 3 s horizon caps "all 3 s"; some ghosts may stay right much longer.
- Results depend on the model, senses and decoder (ADR-0016, ADR-0028, ADR-0036).

## Decision
Keep `perturb.py`, `horizon_study.py` and `plot_horizon.py` as the instruments for Result 1, and treat these numbers as a first pass, reported with the limits above.

## Consequences
- For the viewer's knowledge slider, the most telling settings are discrete: one missed spike, 99.9% vs 99% observed, and voltage error around 0.01–0.1 mV.
- The finding fits the divergence studies: the brain forgets small differences unless they land on a threshold.

## For learners
Laplace's demon needs to know everything. We asked how much "everything" really is for a fly brain. The surprising answer: not the decimals of every voltage, but every spike. Miss one spike at the wrong moment and the prediction fails within a twentieth of a second; blur every voltage by a thousandth of a millivolt and it never does.
