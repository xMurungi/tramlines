# 0048 — Result 3: one spike rarely changes what the fly does, and when it does, our decoder matters

- Status: Accepted (delegated; Result 3 of the owner-adopted ADR-0035), run as pre-registered in [`docs/science/atlas-plan.md`](../science/atlas-plan.md) (merged in PR #28 before the study ran)
- Date: 2026-10-24
- Phase: 5
- Decider: Claude (delegated)

## Context
How often does a single extra spike change what the fly does, where and when, and do those tipping points survive changes to our decoder (CLAUDE.md, Result 3)?

## Options considered
1. Run the plan as written and report every hypothesis (chosen).
2. Adjust the analysis after seeing data. Rejected: that is what pre-registration prevents.

## Decision
Ran the plan: 24 cells (seeds 0–2 × 8 moments), 61,848 extra spikes screened for 30 ms (61,843 made; 5 refused by the engine), 2,160 followed for 3 s, 477 decoder reruns. Code `scripts/atlas_study.py`, `scripts/analyse_atlas.py`; data `docs/assets/atlas_{screen,outcomes,decoder}.csv`, summary `docs/assets/atlas_summary.txt`. 4 h 21 min on 2 workers; memory pressure normal, thermal nominal.

## Results (Wilson 95% intervals; seeds 1–2 alone give the same verdicts)
| Hypothesis | Result | Verdict |
|---|---|---|
| **H1** random cascade ≤ 15% at every moment | 2.8–7.6% per moment | supported |
| **H2** non-cascades change the choice ≤ 5% | 1/720 (0.0–0.8%) | supported |
| **H3** inputs cascade more than random | 3,504/6,644 (52.7%) vs 2,141/47,999 (4.5%) | supported |
| **H4** ≥ 50% of cascades leave the choice unchanged | 1,300/1,440 (90.3%; 88.6–91.7%) | supported |
| **H5** ≥ 70% of tipping points survive each decoder variant | thresholds ×0.8: 87/87; ×1.2: 53/87 (61%; 50–71%); 100 ms window: 11/87 (13%; 7–21%) | **not supported** (×1.2, window) |

**E2, how often a random extra spike changes the fly's choice:** 0.59% pooled (bootstrap 0.46–0.73%). By moment: 0% at 250, 2,250 and 3,750 ms; 0.13–0.86% at 750, 1,750, 2,750, 3,250 ms; **2.84% (2.02–3.71%) at 1,250 ms, on the laced food**.

**E3, where:** cascades come mostly from central neurons (13% of those nudged), ascending and descending neurons (19–27%); optic-lobe neurons, the largest class, almost never cascade (0.2%). Of the random-group spikes that changed the choice, 35 were central, 9 visual projection, 4 ascending, 2 descending, 1 sensory.

## What it means
1. **Most single spikes vanish.** About 95% of random extra spikes change no other spike within 30 ms.
2. **Many brain futures, one behaviour.** Even when a spike ripples through the brain, 90% of the time the fly's choices stay the same (secondary: 23% change the path by > 0.1 mm).
3. **When it matters, it matters at decisions.** The rate is highest on the laced food, zero at three of eight moments, consistent with Result 1.
4. **Tipping points depend on how we read the brain (H5).** With the same thresholds lowered, every tipping point survives; raised 20%, 61% survive; with a slower 100 ms readout, only 13% do. Much of a single spike's power to change behaviour runs through our decoder's sensitivity (a 50 ms rate window near a threshold), not through the brain alone. This is the main caveat of Result 3 and of the free-will fan.

**In one sentence:** one extra spike rarely changes what this fly does (about 1 in 170 at random, about 1 in 35 at the laced-food decision), and whether it does depends strongly on how we translate brain activity into movement.

## Deviations
- The planned figure (`atlas.png`) was not made yet (token budget); the numbers above and in `atlas_summary.txt` are complete. To add.
- The London et al. comparison (spikes caused in the injected neuron's direct targets) needs a new exploratory run; not done.

## Limits
This model only (honesty page); 3 seeds; one dish; 3 s horizon; the decoder is ours. Prior work: London et al. 2010 (one spike in rat cortex), Monteforte & Wolf 2012 (stable chaos), see literature notes.

## For learners
We nudged one brain cell at a time, 62,000 times, and asked whether the fly would choose differently. Almost never, except at the moment it was deciding about food. Then we checked our own measuring tool: read the brain a little more slowly, and most of those "decisive" nudges stopped mattering. A good experiment tests its own instruments, and this one taught us that.
