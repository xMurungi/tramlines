# 0035 — Proposal: an honest Laplace's demon

- Status: Proposed — awaiting owner (changes the concept, CLAUDE.md 1.1, and the v1.0 Definition of Done)
- Date: 2026-10-23
- Phase: 4
- Decider: Owner
- Source: review in GitHub issue #14 (with #11–#13, the conversation it came from)

## Context
A review of the repository (issue #14) found that the headline experience rests on three things the project's own ADRs already document:

1. **The ghost is right by construction:** same code, same state, same random numbers. 100% is what deterministic means ([ADR-0030](0030-projection-not-live.md), [ADR-0033](0033-phase-4-architecture.md) correction).
2. **Forward speed is our input read back out:** P9 is both driven ([ADR-0028](0028-senses-and-decoder-chosen.md)) and read for speed.
3. **"Free will" works only at edges we placed:** random extra spikes almost never matter ([ADR-0029](0029-divergence-batching-monitoring.md)); the decision points were calibrated and placed ([ADR-0032](0032-decision-points.md)), and the shadow's flip is one spike wide against a decoder threshold.

None of this is hidden, but the demo's emotional payoff depends on viewers not knowing it. The builder checked each point against the code and agrees with 1–3. Two smaller claims in the review were mistaken. Lock L7 vs L9 is not a hard conflict: CLAUDE.md Phase 7 already accepts float32 in the browser with determinism *within* the browser. And the repository is private, not public.

## Options considered
1. **Keep the concept as is**, with stronger disclaimers. Cheapest, but anyone technical sees through the 100% meter within a minute, and credibility (L10) suffers.
2. **Reframe: "How much must you know about a brain to predict it, and where does that knowledge stop mattering?"** (the review's proposal, recommended). The perfect ghost stays, shown openly as the control; three measured results become the product:
   - **Predictability horizon:** give the ghost slightly imperfect knowledge (10⁻¹²…10⁻³ mV voltage error, one dropped in-flight spike, float32 rounding, a fraction of neurons observed) and measure how long it stays right. A viewer slider: "how much does the ghost know?"
   - **The brain's contribution:** make inputs and readouts disjoint (with a test), and compare the real connectome with a degree-preserving shuffled "null brain" under the same senses and decoder.
   - **A perturbation atlas:** sweep single-spike injections across neurons and moments; report the fraction that change behaviour, where the leverage is, and whether the tipping points survive decoder changes (100 ms window, thresholds ±20%). Lead with "many brain futures, one behaviour".
3. **Drop the ghost and show only the fan.** Simpler, but loses the hook.

## Recommendation
Option 2. It keeps the Devs chill ("the ghost is right until it knows one spike too little") and turns each weakness into a number nobody has yet. A whole-brain, connectome-constrained, closed-loop version may be new, but that needs a literature check first (London et al. 2010, *Nature*; van Vreeswijk & Sompolinsky 1996).

**A finite v1.0:** the three results above, the viewer with the control ghost, a knowledge slider and the fan, and a long-form write-up with data and scripts.

## Consequences, if accepted
- CLAUDE.md 1.1, 1.3 (Definition of Done) and Phases 5–7 change: the owner's file.
- The walking drive and speed readout must change so that no neuron is both driven and read. That is a sensory/motor choice, Reserved, and the review suggests driving upstream of P9.
- Phase 7: ship precomputed runs plus a browser player, not a live in-browser engine (resolves the L7/L9 tension; owner decision).
- Process: the review also recommends parking The Book "from zero" as a separate project, writing ADRs only for expensive-to-reverse decisions, adding CI and choosing a licence. Each is the owner's call.

## Done already, without a decision (honesty, L10)
- The honesty page now says speed is our drive read back, and explains that the ghost is the control.
- The viewer's caption and bottom line say the same.
- ADR-0033 carries a dated correction.
- The nine code bugs in the review are fixed (issue #14, Part 4).

## For learners
A machine that predicts a deterministic simulation perfectly is not impressive: it is copying. The impressive question is how much a predictor can afford *not* to know. Asking it honestly turns a magic trick into an experiment.
