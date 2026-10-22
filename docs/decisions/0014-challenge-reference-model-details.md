# 0014 — Challenge: the reference code differs from CLAUDE.md section 7.2 in five details

- Status: Challenge
- Date: 2026-10-22
- Phase: 0
- Decider: Claude (delegated) — owner acknowledgement requested

## Context
CLAUDE.md section 7.2 gives the LIF equations "as commonly reproduced" and says: *if the reference code disagrees with this table, the reference code wins; write a Challenge ADR noting the difference.* Reading `model.py` in `philshiu/Drosophila_brain_model` (commit `91bdd1e7`) in Phase 0, every **parameter value** in the table matches. Five **model details** do not. This ADR records them now, before Phase 1 code is written, so nothing is decided by accident.

| # | CLAUDE.md section 7.2 says | Reference code (`model.py`) does |
|---|---|---|
| 1 | Poisson input events raise the target's **g** like a synaptic spike | Poisson events add `w_syn × f_poi = 0.275 mV × 250 = 68.75 mV` directly to **v**. That is about ten times the 7 mV gap between rest and threshold, so every input event makes the target fire. |
| 2 | Every neuron has refractory period t_ref | Poisson-stimulated neurons have refractory period **0** (`neu[i].rfc = 0 * ms`). |
| 3 | On a spike, v ← V_reset | On a spike, v ← V_reset **and g ← 0**. |
| 4 | During refractory, v is held at V_reset | During refractory **both v and g stop evolving** (`(unless refractory)` on both equations). Incoming synaptic spikes still add to g during that time, which is how Brian2 handles `on_pre` events. |
| 5 | Spike when v ≥ V_th | Spike when **v > V_th** (strict). |

Two smaller notes, not disagreements:

- The reference integrates with Brian2's `method='linear'` (exact solution of the linear equations over each step). Eon's PyTorch port uses a forward-Euler step. Which update rule we use is a Phase 1 question (see the [reference model notes](../science/reference-model-notes.md)).
- `model.py` defaults to 150 Hz stimulation; the example notebook text and Eon's sugar experiment use 200 Hz. Both are inside the 150–200 Hz range in section 7.2.

## Options considered
1. **Follow the reference code exactly** (as section 7.2 instructs). Reproduces the validated model; the sugar → MN9 test (section 7.3) becomes a fair test of our engine.
2. **Follow CLAUDE.md section 7.2 as written.** Poisson input into g at 0.275 mV per event would barely move the target, so sugar stimulation would likely fail to drive MN9, and we would not be running the published model.
3. **Follow the reference, but treat Poisson input as a "sensory synapse" into g with a rescaled weight.** Arguably more biological, but it changes the published model, which is Reserved.

## Decision
Proposed: implement Option 1 in Phase 1, exactly as the reference code behaves, since section 7.2 already says the reference code wins. The verified parameter and equation table will go into its own ADR in Phase 1 alongside `tramlines/brain/params.py`.

The owner is asked to **acknowledge** this, and to say whether CLAUDE.md section 7.2 should be updated (changes to CLAUDE.md are Reserved).

## Consequences
- A stimulated sensory neuron in this model fires at roughly the stimulus rate, by construction. That is a fact worth saying on the honesty page: "stimulation" means "make these neurons fire at this rate", like optogenetics, not "deliver sugar to a receptor".
- Point 4 matters for determinism and forking: the refractory timer, and whether g is frozen, are part of the state that a fork must copy.
- The integration-method question (exact vs Euler) is left for Phase 1, with measurements.

## For learners
When a paper and its code disagree, trust the code: it is what actually produced the published results. The disagreements here are small to read and large in effect. Detail 1 alone is the difference between a fly that tastes sugar and one that does not. Chapter 18 shows what happens when you get it wrong.
