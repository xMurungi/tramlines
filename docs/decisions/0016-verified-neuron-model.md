# 0016 — The neuron model, verified against Brian2 spike for spike

- Status: Accepted (delegated)
- Date: 2026-10-22
- Phase: 1
- Decider: Claude (delegated). The owner is asked to acknowledge it with ADR-0014 ([owner decisions](../owner-decisions.md), item 1).

## Context
CLAUDE.md 7.2 says to verify each parameter against the reference code, and that the reference code wins. [ADR-0014](0014-challenge-reference-model-details.md) listed five places where the code differs from 7.2, from *reading* it. Reading is not enough: what matters is what Brian2 actually does when it runs that code. So in Phase 1 we installed Brian2 2.10.1 in a throwaway environment and asked it directly.

## What Brian2 does (measured, not assumed)

1. **Order within each 0.1 ms step** (from `Network.scheduling_summary()`): integrate the state → threshold → deliver synaptic spikes → Poisson input → reset.
2. **Integration is exact.** Brian2's `linear` method generates the closed-form solution over one step:
   `g' = g·e^(−dt/τ_syn)` and `v' = V_rest + (v − V_rest)·e^(−dt/τ_m) + g·τ_syn/(τ_m − τ_syn)·(e^(−dt/τ_m) − e^(−dt/τ_syn))`.
3. **Refractoriness** lasts `timestep(t − lastspike) ≥ timestep(t_ref)` steps (22 steps for 2.2 ms), with v and g frozen.
4. **A refractory neuron ignores input.** Synaptic arrivals (`g += w`) are *discarded*, not stored, while the target is refractory, including during the step in which it fires. A two-neuron probe showed this directly; a control with a non-refractory target received the same spike normally. This **corrects ADR-0014, detail 4**, which predicted that arrivals would still add to g.
5. **The reset's stray `w = 0`** (in `model.py`) assigns to a temporary variable and has no effect.
6. **Delay** is exactly 18 steps.

## Options considered
1. **Reproduce Brian2's behaviour exactly**, including detail 4, and prove it with golden files.
2. **Euler integration, as Eon's PyTorch port does.** Simpler to teach, but not the reference model, and not bit-comparable with Brian2.
3. **Store refractory arrivals in g** (my reading in ADR-0014). Measured to be wrong.

## Decision
Option 1. The verified parameters live in `tramlines/brain/params.py`:

| Parameter | Value | Reference name |
|---|---|---|
| V_rest | −52 mV | `v_0` |
| V_reset | −52 mV | `v_rst` |
| V_th (spike if v > V_th, strictly) | −45 mV | `v_th` |
| τ_m | 20 ms | `t_mbr` |
| τ_syn | 5 ms | `tau` |
| t_ref | 2.2 ms (22 steps); 0 for Poisson-stimulated neurons | `t_rfc` |
| t_delay | 1.8 ms (18 steps) | `t_dly` |
| w_syn | 0.275 mV per synapse | `w_syn` |
| Poisson event | adds w_syn × 250 = 68.75 mV to v | `f_poi` |
| dt | 0.1 ms | Brian2 default |

## Evidence
`scripts/reference/brian2_golden.py` builds two random 400-neuron networks (about 7,800 connections each, random starting voltages and inputs, no randomness during the run) and runs them in Brian2 for 500 ms. `tests/test_engine_vs_brian2.py` runs our engine on the same networks: **every one of about 12,300 spikes per network is identical in neuron and step**, and final voltages agree to within 10⁻⁹ mV (the remaining difference, about 10⁻¹² mV, is rounding from summing in a different order). Before detail 4 was fixed, the same comparison found about 4% extra spikes, so the test does detect real model differences.

## Consequences
- The engine is the reference model, not an approximation of it, at least on these networks. The full-brain check is statistical (sugar → MN9, [ADR-0020](0020-sugar-mn9-regression-bands.md)).
- Refractory state is part of what a fork must copy (`last_spike_step`, Phase 2).
- CLAUDE.md 7.2 is now known to be inaccurate in several details; rewriting it is the owner's call.

## For learners
When a paper and its code disagree, trust the code. When you are unsure what the code does, *run it and look*. Here, reading the code suggested one behaviour and running it showed another. A tiny two-neuron experiment settled it in seconds. Chapter 18 tells this story.
