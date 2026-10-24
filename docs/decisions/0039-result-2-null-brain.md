# 0039 — Result 2: the behaviour lives in the wiring, and survives a lot of damage to it

- Status: Accepted (delegated; Result 2 of the owner-adopted [ADR-0035](0035-proposal-honest-laplaces-demon.md))
- Date: 2026-10-24
- Phase: 5
- Decider: Claude (delegated)

> **Prior work (note added 2026-10-24):** Shiu et al. 2024 already tested shuffled wiring: with connection weights shuffled (global weight distribution kept), sugar drove MN9 in 1 of 100 simulations against 100% with the real connectome. Finding 1 below repeats that result with a different null and at the level of behaviour; what this ADR adds is the closed loop, the partial-rewiring sweep, the convergence measurements and the decoder-free check. See [literature notes](../science/literature-notes.md).

## Context
ADR-0035 asks what the real connectome contributes: the same senses, decoder and arena on the real wiring and on a degree-preserving shuffle of it (a "null brain"). In the demon's terms: a demon that knows every neuron, and how many connections each makes, but not *who connects to whom*, what can it predict? And how wrong can its wiring map be?

## Options considered
**Which null brain.**
1. **Shuffle the receivers, keeping each connection's sender and weight** (a degree-preserving rewiring, the standard network null). Keeps every neuron's out-degree and in-degree, each neuron's outgoing weights, and so its sign (every FlyWire neuron is purely excitatory or inhibitory). Loses who connects to whom, and the balance of excitation and inhibition each neuron receives.
2. **Also keep each neuron's total input weight.** A stronger null, closer to the real brain; harder to build exactly, and a second step after option 1.
3. **Shuffle only within cell classes.** Keeps coarse anatomy; tests fine wiring only. Needs class choices, which are judgement calls.
4. **Completely random wiring (Erdős–Rényi).** Loses even the degrees, so a difference could come from hub neurons alone. Too weak a control.

**How to test it.** An arena run alone would test only walking (a null fly that never walks never meets food), so each brain also gets **clamped probes**: the fly held in place for 1 s on walking ground, food, bitter, food laced with bitter (both at full strength), and under a full looming shadow, with the same senses and decoder.

## Decision
Option 1 (the degree-preserving rewiring of Maslov & Sneppen 2002), in `tramlines/brain/null.py` (`shuffled(connectome, seed, fraction=1.0)`). Permuting the receiver column keeps both degrees; the 0.4% of connections that become self-connections or repeated pairs (none exist in v783) are repaired by swaps, which also keep degrees. `fraction` rewires only a random share of connections, among themselves. Tests: `tests/test_null.py`. Studies: `scripts/null_brain_study.py` (arena, probes, convergence) and `scripts/decoder_free_study.py`; figures `scripts/plot_null_brain.py`. Data in `docs/assets/null_brain*.csv` and `decoder_free.csv`.

## What is confirmatory and what is exploratory
- **Planned (ADR-0035):** real against full null brains. Run first, as designed: real ×3 seeds, 5 null brains ×3 seeds.
- **Added after seeing data:** the clamped probes (after a smoke run showed the null fly never moves); the partial-rewiring sweep (because a full shuffle destroys everything and so says little); the 75% and 90% points; the behaviour cut-offs in the sweep figure. Treat these as exploratory.
- **Written before results:** predictions for the 75%/90% points and for the decoder-free test, in [`docs/science/null-brain-predictions.md`](../science/null-brain-predictions.md). 9 of 10 sweep predictions held (the miss: walking survives at 90%, 2 of 3); the decoder-free predictions held.
- **Raised by the owner:** "is this making the experiment fit our thoughts?" The readouts and decoder were calibrated on the real brain, so a null brain is judged by a yardstick made for the real one. The decoder-free test was added to answer that.

## Findings

![Left: with the fly held in place, the key readout for each situation. Real wiring: P9 about 28 Hz on walking ground, MN9 about 65 Hz on food, MN9 near 0 on bitter and laced food, GF about 45 Hz under the shadow. Null brains: every readout 0 Hz in every situation. Right: the strongest drive any single neuron gets from each sense, on a log scale with the 7 mV threshold; real wiring 51 to 1,289 mV, null brains 13 to 28 mV.](../assets/null_brain.png)

**1. Full null brains do nothing the body can see.** Real wiring (3 seeds): walks about 70 mm, reaches the food, feeds about 5 s, escapes the shadow, 3/3. Null brains (5 shuffles × 3 seeds): never move, 15/15. Held in place, every readout of every null brain is exactly 0 Hz in every situation; the real brain walks (P9 26–31 Hz), feeds (MN9 65 Hz), refuses bitter and laced food (MN9 ≤ 0.5 Hz) and jumps under the shadow (GF about 45 Hz), 3/3 each.

**2. Why: convergence.** The 21 sugar neurons make about 1,500 connections. In the real brain they land on 289 neurons; in a null brain on about 1,520. Summed onto one neuron at the senses' rates, the strongest real receiver gets a mean rise of 96 mV (sugar), 144 mV (bitter), 1,289 mV (looming, mostly onto the escape circuit), 51 mV (walking drive); in null brains 13–28 mV. Null brains still push some first-synapse neurons past threshold (the walking drive pushes 13, the real brain 14). The signal starts in both; only the real wiring gathers it.

**3. The signal travels in the real brain and stops in the null one: the decoder-free test.** Ignoring readouts and decoder, neurons that respond to a sense (≥ 5 Hz above walking ground on average and in every seed; the 1 and 10 Hz cut-offs give the same picture):

| | real | full null (5) | 10% rewired | 50% rewired | 90% rewired |
|---|---|---|---|---|---|
| Food-responsive, 2+ synapses from the sense | 216 | 0–22 | 210–242 | 43–126 | 2–22 |
| Shadow-responsive, 2+ synapses | 214 | 2–15 | 137–160 (one brain: 7,980) | 6,300–6,800 (runaway) | 12–35 |
| Readout neurons responding (food + shadow) | 6 | 0 | 6 | 6–10 | 0–1 |
| Situation read from neurons 2+ synapses from any input (held-out seed) | 12/12 | 10–12/12 | 12/12 | 11–12/12 | 10–12/12 |

Null brains are **not empty**: which situation they are in can still be read from their activity, so "random wiring carries no information" would be wrong. But their sense-specific activity reaches a few dozen neurons, mostly one synapse from the sense, and stops. Real wiring carries it to hundreds of neurons two and three synapses deep, and into the neurons that move the body. The null fly's failure is not only our yardstick.

![Five panels against the share of connections rewired (0%, 1%, 5%, 10%, 25%, 50%, 75%, 90%, 100%), one dot per brain. Median walking stays near 70 mm up to 75% and falls to about 35 mm at 90% and 0 at 100%. Feeding on food holds up to 25% and is gone by 75%. Refusing laced food fails from 5% to 25%. The escape neuron's drive fades from 50%, the escape itself from 75%. Arena activity is about 1,200 neurons at 0–1%, jumps to about 10,000 in many brains between 5% and 50%, and falls below 1,000 from 75%.](../assets/null_brain_sweep.png)

**4. Behaviour survives a lot of wiring damage, and the subtle decision breaks first (exploratory; 3 null brains per share, seed 0).**

| Rewired | walks | feeds on food | refuses laced food | escapes | stays quiet |
|---|---|---|---|---|---|
| 0% (real) | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| 1% | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| 5% | 3/3 | 3/3 | **1/3** | 3/3 | 2/3 |
| 10% | 3/3 | 3/3 | **0/3** | 3/3 | 1/3 |
| 25% | 3/3 | 3/3 | **0/3** | 3/3 | 1/3 |
| 50% | 3/3 | 2/3 (weak) | 2/3 | 3/3 | 0/3 |
| 75% | 2/3 | 0/3 | 3/3* | 2/3 | 2/3 |
| 90% | 2/3 | 0/3 | 3/3* | 1/3 | 3/3 |
| 100% | 0/15 | 0/15 | 15/15* | 0/15 | 15/15 |

\* Hollow: these brains cannot feed at all, so there is nothing to refuse.

- Walking, feeding and escape (each one sense driving one readout) survive rewiring a quarter of all 15 million connections.
- Weighing two senses against each other (bitter vetoing sugar) is the first thing to break, from 5%.
- Between 5% and 50%, many rewired brains tip into **runaway activity**: about 10,000 neurons active instead of about 1,200, often triggered by the shadow. The real wiring stays quiet; partly scrambled wiring does not.
- The fall is graceful, then a cliff between 50% and 100%.

**In one sentence:** a demon that knew every neuron but not its wiring would predict nothing; one whose wiring map is a quarter wrong would still predict walking, eating and escaping, but not the fly's decision about bitter-laced food.

## Limits
- **The yardstick:** senses, readouts and decoder were chosen and calibrated on the real brain. The decoder-free test reduces this concern but does not remove it: "responds to a sense" and "synapses from the sense" are still our measures.
- **One kind of null.** A null that also keeps each neuron's input balance (option 2) may behave differently, especially in the runaway range.
- **Small samples.** 3 seeds for real and full null brains; 3 null brains and one seed per rewired share. Read 2/3 as "most", not as 67%.
- Probes use full-strength stimuli held for 1 s; the arena is the default dish. Results depend on the model, senses and decoder (ADR-0016, ADR-0028, ADR-0036).
- Cost: full study 15 min, sweep 22 + 9 min, decoder-free 14 min, all on 2 workers. The decoder-free run pushed swap from 1.85 to 3.99 GB (memory pressure "warning", 35% available) because runaway brains use up to 6.4 GB; reruns of rewired brains use 1 worker.

## Consequences
- The honesty page can now say that the sense-to-movement pathways come from the measured wiring, with evidence.
- The "laced food" decision point (ADR-0032) is the most wiring-sensitive behaviour, consistent with Result 1, where it was also the least predictable moment.
- The runaway activity in partly rewired brains suggests the real wiring is balanced in a way random wiring is not. A null with input balance kept (option 2) would test that; a candidate follow-up.

## For learners
To show that something depends on a cause, take the cause away and keep everything else. Here we kept every neuron, every connection count and every synapse weight, and only scrambled who connects to whom. The fly stopped doing anything. Then we scrambled only part of the wiring and found it is surprisingly tough: a quarter scrambled, it still walks, eats and escapes. What breaks first is its judgement, eating food it should refuse. And when the owner asked whether we were bending the test to fit our expectations, we built a second test that did not use our own measuring stick. See [Chapter 26](../book/ch26-senses-in-movement-out.md).

## Note after the literature check (2026-10-24)
Candidate explanations for the convergence and the runaway activity, to test rather than assume: the rich club and reciprocity of FlyWire wiring (Lin et al. 2024) and inhibitory hubs (Li et al. 2026). A public embodied project reports that scrambling the wiring stops its fly steering (fly-brain-zero-shot), a neighbour of finding 1. See [literature notes](../science/literature-notes.md).
