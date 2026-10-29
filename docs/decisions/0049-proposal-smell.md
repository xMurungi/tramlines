# 0049 — Proposal: smell, so the fly can find food from a distance

- Status: **Proposed — awaiting owner** (owner decision 32). Which neurons count as senses is Reserved (CLAUDE.md 2.2, section 8).
- Date: 2026-10-29
- Phase: 5
- Decider: Owner

## Context
The fly can only taste on contact (ADR-0028), so it never heads towards food; in an empty dish it walks straight and then follows the wall, turned by a body rule, not by its brain (ADR-0036; honesty page). Real flies find food by smell. The FlyWire v783 annotations contain **2,281 olfactory receptor neurons** (1,117 left, 1,134 right, 28 unassigned) in **51 glomerulus types** (`hemibrain_type`, e.g. ORN_DM1: 68 neurons, ORN_VA2: 67, ORN_DM2: 54, ORN_DM4: 40).

## The question
Does this untrained, wiring-only brain steer towards a food odour? Its smell neurons reach the turning neurons only through several brain areas (antennal lobe, lateral horn, mushroom body); whether the signal arrives, and with the right left/right sign, is unknown. **If it steers, that is a new finding; if it does not, that is an honest result, and steering is not added to the body to fake it.**

## Options considered
1. **Food odour on attraction glomeruli, left/right from the two antennae** (recommended). Each food patch emits an odour that fades with distance; each antenna samples it at its own position; the receptor neurons of glomeruli known to mediate attraction to food odours (candidate: DM1 and VA2 for vinegar, per Semmelhack & Wang 2009, *Nature*; to verify in a literature check) are driven at rates proportional to the odour on each side. Steering, if any, comes from the existing turning readout (DNa02).
   - Pros: minimal, literature-anchored, measurable. Cons: most receptor neurons project to *both* antennal lobes, so left/right differences may be weak in the model; one odour only.
2. **A broader odour code** (several glomeruli with an odour-specific pattern). More realistic, more choices without data to anchor them.
3. **Do not add smell.** Keep the dish as is; accept wall-following as the body rule it is.

## Recommended plan (if adopted)
1. **Literature check:** which glomeruli and receptor rates for a food odour (e.g. vinegar); bilateral projection of receptor neurons.
2. **Survey (exploratory), before any change to the world:** with the fly held still, drive the chosen receptor neurons on one side only, at several rates, and measure the turning readout (DNa02 left vs right) and the walking readout (P9). Can run in the cloud (Actions → run study).
3. **Pre-registered plan** (merged before the study), then the study: does the fly, released at several distances and angles, approach the odour source more often than with smell off? Criteria fixed in advance; the null brains (ADR-0039) as a control.
4. **Then the world:** odour fields around patches, senses port, tests, determinism gate, recalibrated decision points, honesty page.
- Estimated size: 2–4 sessions, plus computing (survey ~1 h; study a few hours, or less in the cloud).

## Consequences, if adopted
- The fly could search and approach instead of circling, if its brain supports it; the viewer would look more alive.
- A new sense means re-checking earlier results that depend on the dish (Results 1, 3, 4 used the current dish; they stay valid for it, and new runs would say which dish they use).
- Honesty page: what is our design (odour physics, which neurons) and what is the brain's (whether it steers).

## For learners
Our fly can taste food only by stepping on it, so it never goes looking. Real flies follow smells. The fly's brain map includes over two thousand smell neurons, but nobody knows whether a brain built only from wiring, never trained, will turn towards a smell. The proposal is to ask the brain, measure the answer, and accept it whichever way it goes.
