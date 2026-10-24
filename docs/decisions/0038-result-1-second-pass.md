# 0038 — Result 1, second pass: what the ghost must know depends on when it looks

- Status: Accepted (delegated; Result 1 of the owner-adopted [ADR-0035](0035-proposal-honest-laplaces-demon.md))
- Date: 2026-10-24
- Phase: 5
- Decider: Claude (delegated)

## Context
The first pass ([ADR-0037](0037-result-1-predictability-horizon.md)) measured how long an imperfect ghost stays right, but only once per case: one seed (one run of the brain) and one random draw of each error. A single measurement cannot tell a rule from luck. This pass repeats every case so each one becomes a distribution, and looks more finely at the edge the first pass found (voltage error between 0.01 and 0.1 mV, observation between 99% and 99.9%).

## Options considered
1. **More seeds and draws at the same three moments**: 3 seeds × 3 moments × 3 draws of every random error. Pros: directly answers "rule or luck?", reuses the instruments unchanged, and the first pass's cases are contained in it, so it checks itself. Cons: about 80 minutes of computing on two workers.
2. **Many more moments on one seed** (a scan through time). Pros: shows how predictability varies along a run. Cons: still one brain run, so it cannot separate a property of the model from a property of seed 0.
3. **A longer horizon (10 s)**. Pros: removes the 3 s cap. Cons: more than three times the cost per run, and most failures happen within half a second, so the cap rarely binds.

## Decision
Option 1. `scripts/horizon_study.py` gains `--seeds`, `--draws`, `--set v2` and `--tag`; with no options it still reproduces the first pass. The v2 set: the control; voltage error 0.001, 0.01, 0.03, 0.1 and 1 mV; float32; one missed in-flight spike; 99.9%, 99.5% and 99% of neurons observed. Errors that do not involve chance (control, float32) run once per seed. 270 runs of 3 s; data `docs/assets/horizon_v2.csv`, figure `docs/assets/horizon_v2.png` (`scripts/plot_horizon.py --tag v2`).

**Self-check:** seed 0 with draw 0 uses exactly the first pass's errors. All 27 cases the two passes share came out identical, field for field.

![Three panels (walking, laced food, shadow), one dot per ghost, with the count of ghosts right for all 3 s. Walking: nearly every ghost stays right except voltage error of 1 mV (2/9). Laced food: most kinds fail; even 0.001 mV fails 4 of 9 times; one missed spike fails 9 of 9. Shadow: 0.001 mV and 99.9% observation stay right 9 of 9; 0.03 mV and above, and one missed spike, mostly fail within 50–330 ms.](../assets/horizon_v2.png)

## Findings (second pass: 3 seeds; 9 ghosts per random error, 3 per fixed one)

| The ghost knows… | walking | laced food | shadow |
|---|---|---|---|
| everything (control) | 3/3 | 3/3 | 3/3 |
| float32 precision | 3/3 | 3/3 | 3/3 |
| voltage to 0.001 mV | 9/9 | **5/9** | 9/9 |
| voltage to 0.01 mV | 9/9 | 0/9 | 7/9 |
| voltage to 0.03 mV | 8/9 | 1/9 | 3/9 |
| voltage to 0.1 mV | 7/9 | 0/9 | 1/9 |
| voltage to 1 mV | 2/9 | 0/9 | 0/9 |
| one in-flight spike missed | **9/9** | **0/9** | **1/9** |
| 99.9% of neurons | 9/9 | 6/9 | 9/9 |
| 99.5% of neurons | 8/9 | 4/9 | 6/9 |
| 99.0% of neurons | 6/9 | 2/9 | 4/9 |

Ghosts right for all 3 s (paths within 0.1 mm). When a ghost fails, it fails fast: median 78–347 ms, range 36–537 ms.

1. **The missed spike holds up, and is the sharpest result.** Missing one spike in transit never matters while the fly walks (9/9 right) and almost always matters at a decision point (laced food 0/9, shadow 1/9, wrong within 52–359 ms).
2. **The first pass was too kind to small voltage errors.** At the laced food, voltages known to a thousandth of a millivolt still failed in 4 of 9 ghosts (within 177–347 ms), and 0.01 mV failed in all 9. Seed 0, the only seed of the first pass, happened to be one where 0.001 mV survived. At this decision there is no "good enough" voltage precision within the range tested.
3. **Float32 is always enough** (9/9 runs across moments). Its error is far smaller than 0.001 mV (about 10⁻⁶ mV at these voltages).
4. **Timing matters more than precision.** The "walking" ghosts start at 0.5 s and run 3 s, so they pass through the same laced food and the same shadow as the others, yet with 0.01 mV error they stay right 9/9 and with a missed spike 9/9. The same errors made *at* the decision fail almost every time. A difference made while the brain is not deciding fades within the ~0.7 s before the fly reaches the food; a difference made on the edge does not. This matches the divergence studies ([ADR-0036](0036-walking-drive-upstream-of-p9.md)): the brain forgets small differences unless they land on a threshold.
5. **Seeing 99.9% of neurons is not quite enough at the laced food** (6/9; about 140 neurons unseen). Elsewhere it is.

**In one sentence:** what a demon must know depends on when it looks; while the fly walks, rough knowledge foresees it for seconds, but at a decision even a thousandth of a millivolt or one spike in flight can be the difference.

## Limits
- Three seeds, three moments, three draws: distributions, but small ones. The counts are what was observed, not population rates; read 5/9 as "about half", not as 56%.
- The three moments are fixed in time, so the fly's situation at a moment differs a little between seeds: at 1.2 s on the laced food, seed 1's fly is already feeding while seeds 0 and 2 are about to decide. At 3.35 s all three are at the dish wall under the shadow. Recorded per row in the CSV (`fly_at_moment`).
- "Partial" still assumes unseen neurons are at rest; the 3 s horizon still caps "right"; everything depends on the model, senses and decoder (ADR-0016, ADR-0028, ADR-0036).
- Computing cost: 79 minutes on two workers (about 35 s of computing per 3 s ghost); perturbed brains keep more neurons awake, which slows the awake-set engine (ADR-0027).

## Consequences
- Findings 1–4 of ADR-0037 stand, except its first: small voltage errors are harmless while walking and under the shadow, not at the laced food. ADR-0037 now points here.
- For the viewer's knowledge slider: the clearest demonstration is the same error made at two moments, once while walking (harmless) and once at the decision (fatal).
- A time scan (option 2) on several seeds would show how predictability rises and falls along a run; it is a candidate for a third pass, after Results 2 and 3.

## For learners
One measurement can fool you. Our first try said a ghost that knows every voltage to a thousandth of a millivolt is always right. Running the same experiment on three versions of the brain, three times each, showed that is true while the fly walks but false at the moment it decides whether to eat. Repeating experiments is how you tell a rule from luck. See [Chapter 22](../book/ch22-the-ghost.md).
