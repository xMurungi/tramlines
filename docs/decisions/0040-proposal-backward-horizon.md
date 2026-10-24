# 0040 — Proposal: the backward horizon (can the demon recover the past?)

- Status: **Proposed — awaiting owner** (owner decision 21). Adding a fourth result changes what the project claims, which is Reserved (CLAUDE.md 2.2).
- Date: 2026-10-24
- Phase: 5
- Decider: Owner

## Context
Laplace's demon, as he described it, would see the past as clearly as the future. His demon could, because Newton's laws run equally well backwards: from the present you can compute the past as surely as the future.

This model's laws do not run backwards. Voltages leak towards rest (like friction), and a neuron that fires is reset to the same voltage however it got there. Both erase information. So the model can be fully deterministic forwards and still have a past that no demon can recover. Results 1–3 measure the demon looking forwards. This proposal measures it looking back.

**The question:** two pasts that differ slightly lead, some time later, to two present states. When can a demon that sees the present perfectly, up to its measuring precision ε, no longer tell which past happened? Call that time the **backward horizon** B(ε). Measure it for the brain alone, and for the brain plus the body.

## Pilot (exploratory; already run, to ground this proposal)
`scripts/backward_pilot.py`: decision dish, seed 0, Result 1's three moments; one small difference made in the past; both timelines run 2 s side by side, compared every 10 ms on the brain's *functional* state (voltages, synaptic inputs, spikes in transit, refractory neurons, random stream; not the engine's last-spike bookkeeping). Data `docs/assets/backward_pilot.csv`. Predictions were written first: [`docs/science/backward-horizon-predictions.md`](../science/backward-horizon-predictions.md).

| Past difference | walking (0.5 s) | laced food (1.2 s) | shadow (3.35 s) |
|---|---|---|---|
| voltages off by 10⁻⁹ mV | brain at the rounding floor¹ by 0.5 s; body same | floor by 0.5 s; body same | floor by 0.5 s; body same |
| voltages off by 10⁻³ mV | floor by 0.5 s; body same | floor by 0.5 s; body same | floor by 0.5 s; body same |
| one spike in transit missed | not made (none in transit²) | brain mV apart for ~1 s, floor by 2 s; **body 0.5 mm apart** | mV apart for ~0.5 s, floor by 2 s; **body 15 mm apart** (one fly jumped) |
| one extra spike | brain still 0.29 mV apart at 2 s; **body 0.36 mm apart** | 10⁻⁸ mV at 2 s; **body 0.15 mm apart** | floor by 2 s; **body 0.75 mm apart** |

¹ **The rounding floor.** No pair ever became identical bit for bit. About 110,000–122,000 voltages stay apart by at most about 7 × 10⁻¹³ mV, whatever the starting difference. This is the computer's arithmetic, not the brain. Near −52 mV a 64-bit number moves in steps of 7.1 × 10⁻¹⁵ mV; each 0.1 ms the leak shrinks a voltage's distance from rest by 0.5%, which is less than half a step once that distance is under 100 steps, so it freezes there (100 × 7.1 × 10⁻¹⁵ = 7.1 × 10⁻¹³ mV, the measured value). In exact arithmetic the difference would shrink forever, never reaching zero. So "erased" has to mean "below what the demon can measure".

² The pilot found a bug: "one missed spike" did nothing when no spike was in transit. Fixed in PR #21; Result 1 corrected (ADR-0038).

**What the pilot suggests:**
1. **The brain forgets, the body remembers.** To any precision coarser than 10⁻¹² mV, the brain erases these pasts within 0.5–2 s. Wherever a difference changed behaviour, the fly's position keeps it: 0.15 to 15 mm, permanently.
2. **The body can keep the brain from forgetting.** While walking, one extra spike shifted the fly 0.36 mm; the shifted body then meets the world slightly differently, and that keeps the brain 0.29 mV apart after 2 s.
3. **My predictions were wrong in two places,** which is why they were written down: I expected bit-identical brains within 0.5–1 s (the rounding floor prevents it), and "never forgets" at decisions (the brain forgets; only the body remembers).

## Options considered
1. **Do it, as the mirror of Result 1** (recommended). Same moments, 3 seeds; differences: voltage 10⁻⁹ to 1 mV (3 draws), one missed spike (only where one is in transit), one extra aimed spike (3 neurons); horizon 3 s. Report B(ε) for ε = 10⁻¹², 10⁻⁹, 10⁻⁶, 10⁻³ mV, for the brain and for brain plus body, next to Result 1's forward horizon. Add one exact-arithmetic check on the small 400-neuron test network (higher precision), to show the rounding floor is the computer's and not the model's. About 160 pairs, roughly 70 minutes on 2 workers.
   - Pros: completes Laplace's demon (future *and* past); cheap; reuses the tools; it may show a clean pattern: in a forgetting brain the past survives in behaviour.
   - Cons: a fourth result to write up and show; the principle (irreversible dynamics erase the past) is long known in physics, so the new part is only the concrete measurement in a connectome model.
2. **A section inside Result 1**, without the full sweep: report the pilot with its limits. Pros: almost free. Cons: one seed, one draw; the same weakness the first pass of Result 1 had.
3. **Do not do it.** Keep v1.0 to the three adopted results. Pros: focus. Cons: the demon stays half-tested.

## Recommendation
Option 1. It costs about an hour of computing and turns a pilot into a distribution, the lesson of Result 1's second pass.

## If adopted
- CLAUDE.md 1.3 (Definition of Done) and Phase 5 gain "Result 4, the backward horizon": owner amendment.
- Honesty: the claim is about this model, which has no learning or memory and so is built to forget quickly; real brains store memories in their wiring. Literature check first (irreversibility and information erasure, e.g. Landauer 1961; work on memory in recurrent networks).
- The viewer's "replay" (White Bear) mode could show it: two pasts, one present.

## For learners
Running a film backwards usually looks wrong: smoke flows back into a candle, a broken glass jumps onto the table. That is because the world loses information as it goes. Our simulated brain does too: its neurons leak and reset, so different pasts fade into the same present. We asked how long a perfect observer could still tell them apart. Within a second or two, it can't by looking at the brain. It can by looking at where the fly is.
