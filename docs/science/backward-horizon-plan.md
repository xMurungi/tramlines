# Result 4, the backward horizon: analysis plan (pre-registered)

- Written: 2026-10-24, before the study's code ran on any data. Merged into `develop` before the study runs; the merge commit is the timestamp.
- Adopted by the owner in [ADR-0040](../decisions/0040-proposal-backward-horizon.md). Results will be reported in ADR-0041, with every deviation from this plan listed.
- **What was already seen:** the pilot in ADR-0040 (seed 0, the same three moments, 2 s). The hypotheses below are informed by it. Seed 0 overlaps the pilot; seeds 1 and 2 are new. Results are reported for all seeds and separately for seeds 1–2.
- A pipeline test on one pair may run before the study, to check the code; its numbers are not analysed.

## Question
A demon sees the present brain (and body) perfectly, up to a measuring precision ε. Two pasts differed slightly at time t₀. After how long can the demon no longer tell which past happened?

## Definitions
- **Pair.** Two timelines loaded from the same saved state at moment *m* of seed *s* on the decision dish: the *truth* T, and the *altered* A, which receives one difference *d* just after loading. Both then run 3,000 ms with the same inputs (same random stream).
- **Brain difference at time t** (sampled every 10 ms): Δv = max over neurons of |v_A − v_T|; Δg = max |g_A − g_T|; **discrete state equal** = spikes in transit equal, refractory neurons equal, random stream equal. (The engine's last-spike bookkeeping is not compared; it matters only during the 2.2 ms refractory period, which "refractory neurons" covers.)
- **Indistinguishable at precision ε at t:** discrete state equal and max(Δv, Δg) < ε.
- **B_brain(ε):** the earliest sample t such that the brains are indistinguishable at ε at every sample from t to 3,000 ms. If none, censored ("> 3 s").
- **Body differs** at 3 s: any field of the fly's state differs (position, heading, feeding, jump cooldown). Distance in mm is reported.
- **B_full(ε):** as B_brain(ε), also requiring the fly's state and the decoder's window to be identical.

## Design
- Seeds 0, 1, 2; moments 500 ms (walking), 1,200 ms (laced food), 3,350 ms (shadow); decision dish; 3,000 ms per pair.
- Differences:
  - voltage noise, σ ∈ {10⁻⁹, 10⁻⁶, 10⁻³, 10⁻¹} mV, draws 0, 1, 2 (`perturb.blur`);
  - one missed spike in transit, draws 0, 1, 2 (not made when none is in transit; reported as not made);
  - one extra spike in a walking-drive neuron (free will, ADR-0031): the first three, by index, that can fire at that moment.
- Up to 162 pairs. Precisions ε ∈ {10⁻¹³, 10⁻¹¹, 10⁻⁹, 10⁻⁶, 10⁻³} mV. 10⁻¹³ lies below the float64 rounding floor found in the pilot (about 7 × 10⁻¹³ to 1.4 × 10⁻¹² mV) and is expected to be always censored; it is included to show the floor.

## Exact-arithmetic check
On the 400-neuron random test network (`tests/_scenarios.py`, `small()`):
1. A reference implementation of the engine's step, written for generic numbers, run in float64 from a saved state, must match the engine bit for bit for 2,000 steps (validates the reference).
2. Two pasts (voltage noise σ = 10⁻⁹ mV) run 1 s in float64 and in 50-digit arithmetic (mpmath), with the same Poisson draws.

## Statistics
- Proportions as n/N with Wilson 95% intervals.
- B(ε) as medians over uncensored pairs with bootstrap 95% intervals (10,000 resamples, seed 0), with the censored count given separately.
- No p-values. Each hypothesis is judged by its stated criterion.

## Hypotheses and criteria
- **H1, the rounding floor.** B_brain(10⁻¹³) is censored in ≥ 90% of voltage pairs. B_brain(10⁻⁹) ≤ 1,000 ms in ≥ 90% of voltage pairs with σ ≤ 10⁻³ mV.
- **H2, the brain forgets spikes.** For spike differences (missed or extra) at laced food and shadow, B_brain(10⁻⁹) ≤ 3,000 ms in ≥ 50% of the pairs made.
- **H3, the body remembers.** For spike differences at laced food and shadow, the body differs at 3 s in ≥ 50% of pairs made. For voltage differences with σ ≤ 10⁻³ mV (all moments), the body differs in ≤ 25%.
- **H4, the body keeps the brain from forgetting.** Among all pairs, B_brain(10⁻⁹) is censored more often when the body differs at 3 s than when it does not (both proportions reported with intervals; supported if the intervals do not overlap, suggestive if only the point estimates differ in that direction).
- **H5, the floor is the computer's.** In the exact-arithmetic check, the float64 difference stops shrinking above 10⁻¹⁴ mV, while the 50-digit difference keeps shrinking below 10⁻²⁰ mV within 1 s.

Each hypothesis is reported as supported, not supported, or not testable (with the reason), whatever the outcome.

## Planned outputs
- `docs/assets/backward_horizon.csv`: one row per pair: seed, moment, difference, made or not, B_brain and B_full at each ε, body distance at 3 s, Δv at 100 ms intervals.
- `docs/assets/backward_horizon.png`: B_brain(ε) per moment and kind of difference, with body-differs fractions; Result 1's forward horizon at the same moments alongside.
- `docs/assets/exact_check.csv` and a panel showing Δv over time in float64 and 50 digits.
- Exploratory analyses beyond this plan are labelled as such.
