# 0031 — Proposal: aim the free-will spike where it can matter

- Status: Accepted — owner approved option 2 (aimed spike at decision moments), 2026-10-23
- Date: 2026-10-22
- Phase: 3 (for Phase 5)
- Decider: Owner (approved 2026-10-23)

## Context
CLAUDE.md Phase 5: "each branch gets one extra spike in a randomly chosen neuron". The divergence study ([ADR-0029](0029-divergence-batching-monitoring.md)) shows this model is strongly stable: a uniformly random extra spike changed nothing else in the brain in 30 of 32 trials, and never changed the path visibly while the fly was walking. Spikes into **sensory input neurons during strong drive** (feeding) diverged in 4 of 16 trials, the first from 235 ms.

## Options considered
1. **Keep it as specified** (any neuron at random). Honest and simple; the fan would almost always be one line. The free-will moment would show "nothing happened", which is itself a statement, but not the experience CLAUDE.md 1.1 describes.
2. **Aimed spike (recommended):** each branch's extra spike goes into a different neuron among those *currently receiving input* (the senses and the walking drive), and the button is offered at **decision moments** (on food, a shadow approaching, a patch edge). Every branch is still exactly one extra spike, logged.
3. **Many-worlds branches:** each branch differs in its future *random input draws* instead (another equally likely sensory stream). Always diverges, and matches the many-worlds idea, but it is chance, not a spike, and less faithful to "one spike, and the future splits".
4. **Give the model background activity** (weak noise into every neuron) so it sits near threshold and perturbations spread. Closer to real brains, but it changes the published model (Reserved) and breaks the reproduction of Shiu et al.

## Recommendation
Option 2 now, measured again on an arena designed with more decision points (next step); keep option 3 as a possible second button ("chance") if option 2's fans are still thin. Not option 4 without a separate scientific review.

## Consequences
- The UI must show *where* the extra spike went (the neuron, its type) and *when*, as part of the honesty of the moment.
- The divergence study gains a "decision moment" scenario to tune the arena before Phase 5.
- If accepted, CLAUDE.md Phase 5's wording should change (the owner's file).

## For learners
A free choice in this model is not a random flicker anywhere in the brain: almost all of those vanish. Choices that matter happen where the brain is already busy deciding something. So we put the extra spike there, and we say exactly where we put it.
