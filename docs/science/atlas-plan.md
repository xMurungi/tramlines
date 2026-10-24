# Result 3, the perturbation atlas: analysis plan (pre-registered)

- Written 2026-10-24, before the study's code existed. Merged into `develop` before the study runs; the merge commit is the timestamp. Results go in an ADR, with every deviation from this plan listed.
- **Already seen:** the pilot (`scripts/atlas_pilot.py`, `docs/assets/atlas_pilot.csv`): seed 0, moments 0.5, 1.2, 2.0 and 3.35 s. The study uses different moments, and seeds 1 and 2 are new. The design and the hypotheses are informed by the pilot, which found: 4–10% of random single spikes cascade within 30 ms (48–64% in driven input neurons); about half of followed cascades changed the path; 1 of 120 screened-out spikes still changed behaviour later. Screening costs about 0.08 s per spike, a 3 s follow-up about 10 s.
- A pipeline test on one cell may run first; its numbers are not analysed.

## Question
CLAUDE.md, Result 3: how often does one extra spike change what the fly does, where (in which neurons) and when; and do the tipping points survive changes to our decoder?

## Definitions
- **Cell:** one seed and one moment on the decision dish (the default walking drive, food laced with bitter, a faint shadow at 3.0–3.5 s; ADR-0032, ADR-0036).
- **Extra spike:** `Brain.inject_spike` on a fork of the cell's state. A spike the engine refuses (refractory, or already fired at that step, ADR-0041) is *not made* and counted separately.
- **Cascade:** at least one spike in the 30 ms after the extra spike differs from the untouched run (`atlas.screen`).
- **Choice:** within the 3 s after the moment, the number of times the fly starts feeding and the number of times it jumps. **Choice changes** when either count differs from the untouched run. (Timing alone does not count: arriving at the food 60 ms later is the same choice.)
- Secondary measures: **behaviour differs** (feeding starts and stops and jumps, matched in order within 50 ms; `atlas.behaviour_differs`) and **path wrong** (more than 0.1 mm apart at any time within 3 s, Result 1's test).

## Design
- Seeds 0, 1, 2 × moments 250, 750, 1,250, 1,750, 2,250, 2,750, 3,250, 3,750 ms: 24 cells. (1,250 ms is on the laced food for most seeds; 3,250 ms is under the growing shadow.)
- **Neuron groups per cell:**
  - *random:* 2,000 neurons drawn uniformly from all 138,639 (the population estimate);
  - *awake:* 300 drawn uniformly from the neurons not exactly at rest at that moment;
  - *inputs:* all 277 driven input neurons (the free-will button's targets, ADR-0031).
  Draws use their own seeded generator (seed × 10,000 + moment, plus 1 for awake).
- **Screen:** every drawn neuron, 30 ms.
- **Follow-up** (3 s, `atlas.outcome`): per cell and group, up to 20 cascades and 10 non-cascades, each drawn uniformly from those screened.
- **Decoder robustness:** per cell, up to 10 spikes whose choice changed under the default decoder, plus 3 followed cascades whose choice did not, rerun from the same moment (untouched and with the spike) under three decoders:
  - **V1:** rate window 100 ms (default 50); the window's earlier 50 ms are rebuilt from the readouts' recorded spikes (checked: rebuilding the default 50 ms reproduces the saved window exactly);
  - **V2:** every threshold ×1.2 (Giant Fiber jump 60 Hz, feeding start 36 Hz, stop 18 Hz);
  - **V3:** every threshold ×0.8 (40, 24, 12 Hz).
  Under each, the spike is a tipping point if the choice differs from that decoder's own untouched run.
- Budget: about 62,000 screens (~45 min on 2 workers), ≤ 2,160 follow-ups (~3 h), ≤ 936 decoder reruns (~1.3 h).

## Estimands
- **E1:** cascade rate per group and moment.
- **E2:** the rate at which a random single spike changes the choice, per moment and pooled: P(cascade)·P(change | cascade) + P(no cascade)·P(change | no cascade), from the random group, with a stratified bootstrap 95% interval (10,000 resamples, seed 0).
- **E3 (where):** the cell types and classes (FlyWire annotations, `super_class`) of random-group neurons that cascade, and of those that change the choice.
- **E4:** for each decoder variant, the fraction of tipping points that survive, and the fraction of non-tipping controls that become tipping points.

## Hypotheses and criteria
- **H1, most spikes die:** the random group's cascade rate is ≤ 15% at every one of the 8 moments (pooled over seeds).
- **H2, the screen misses little:** among followed non-cascades (all groups and cells pooled), the choice changes in ≤ 5%.
- **H3, aiming works:** the inputs group cascades more often than the random group (pooled; Wilson 95% intervals do not overlap).
- **H4, many brain futures, one behaviour:** among followed cascades (all groups pooled), ≥ 50% leave the choice unchanged.
- **H5, tipping points survive the decoder:** for each of V1, V2 and V3, ≥ 70% of default tipping points still change the choice.

Proportions are given with Wilson 95% intervals. Each hypothesis is reported as supported, not supported, or not testable, with the reason. Seeds 1–2 are also reported separately.

## Planned outputs
- `docs/assets/atlas_screen.csv` (one row per screened spike), `atlas_outcomes.csv` (follow-ups), `atlas_decoder.csv` (reruns), `atlas_summary.csv`.
- `docs/assets/atlas.png`: E1 and E2 by moment and group; E4 by variant; E3 as a table in the ADR.
- Anything beyond this plan is labelled exploratory.
