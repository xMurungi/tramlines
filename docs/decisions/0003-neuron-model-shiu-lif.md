# 0003 — Every neuron is a leaky integrate-and-fire unit, as in Shiu et al. 2024

- Status: Locked
- Date: 2026-10-22
- Phase: 0
- Decider: Owner

## Context
A wiring diagram does nothing on its own; we need a rule for how each neuron responds to input. Detailed biophysical models need parameters nobody has measured for 138,000 cells. Shiu et al. (2024, *Nature*) showed that a very simple model on the full connectome predicts real fly behaviour surprisingly well.

## Options considered
1. **Leaky integrate-and-fire (LIF) with Shiu et al. parameters.** Published, validated against experiments, cheap, simple enough to teach in one chapter.
2. **Conductance-based or Hodgkin–Huxley models.** More realistic per cell, but unmeasured parameters for nearly every cell type, far slower, and no validation at whole-brain scale.
3. **Rate models** (no spikes). Faster, but lose spikes, and spikes are what the free-will button injects.

## Decision
We use the LIF model of Shiu et al. 2024 with their parameters, verified against their reference code in Phase 1. Where the reference code and CLAUDE.md section 7.2 disagree, the code wins and a Challenge ADR records it ([ADR-0014](0014-challenge-reference-model-details.md)).

## Consequences
- One parameter set for every neuron: honest to state, easy to explain, clearly a simplification ([ADR-0010](0010-honesty-is-a-feature.md)).
- The Phase 1 acceptance test (sugar → MN9) checks we reproduced it faithfully.
- Changing equations or parameters is Reserved for the owner.

## For learners
A leaky integrate-and-fire neuron is a bucket with a small hole. Input pours water in, the hole lets it leak out, and when the water reaches a line, the neuron "fires" and the bucket is emptied. That is the whole model. Chapter 10 builds one in plain Python.
