# 0001 — The concept is a machine that predicts a fly's future

- Status: Locked; amended by [0035](0035-proposal-honest-laplaces-demon.md) (owner-adopted 2026-10-23): the prediction machine becomes an honest Laplace's demon. The original concept is preserved at tag `v0.4.0`.
- Date: 2026-10-22
- Phase: 0
- Decider: Owner

## Context
The FlyWire connectome has already been used to make a simulated fly play video games. Those demos show that the wiring can be *controlled*. They do not make anyone feel anything about what a copied brain *means*. The project needs one idea strong enough to carry a 30-second clip and a whole book.

## Options considered
1. **Game-playing demo** (fly plays a game). Proven to attract attention, but the space is saturated and the idea is about control, not meaning.
2. **Free-roaming virtual pet** (a fly living in a world). Gentle and approachable, but nothing happens that a viewer could not get from an animation.
3. **Prediction machine**: a live fly plus a ghost copy that runs seconds ahead and is always right, and a "free will" button that splits the future. Novel, buildable with known tools, and it puts a real philosophical question on one screen.

## Decision
Tramlines is the prediction machine: a live fly, a ghost that shows its future, and a free-will button that fans that future into branches (CLAUDE.md section 1.1).

## Consequences
- Determinism is no longer a nice-to-have. It is the product (see [ADR-0007](0007-determinism-first.md)).
- Forking a running brain must be cheap ([ADR-0008](0008-fork-shares-weights.md)).
- The honesty page has to work hard: the concept invites over-reading ([ADR-0010](0010-honesty-is-a-feature.md)).
- Anything that changes this concept is Reserved for the owner.

## For learners
Every project needs one sentence that tells you what to build and what to ignore. Ours is: "a copy of a fly's brain, and a second copy running ahead to show its future." When you are unsure whether to add a feature, ask whether it makes that sentence clearer. Chapter 0 tells this story in full.
