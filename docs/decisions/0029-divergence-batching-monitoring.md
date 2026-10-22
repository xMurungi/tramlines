# 0029 — What one extra spike does, what batching saves, and the machine's limits

- Status: Accepted (delegated; measurements requested by the owner: "do what's best for the mission")
- Date: 2026-10-22
- Phase: 3 (preparing Phases 4–5)
- Decider: Claude (owner-delegated)

## Context
The [vision proposal](https://claude.ai/artifact/YX2bran5jpVRDVtDFxN8Lc) named one key risk: if an extra spike does not visibly change the fly's future within the prediction horizon, the free-will fan collapses into a single line. It also guessed that 8 batched futures would cost about 2× one. Both were measured, with the machine monitored while doing so.

## Divergence study (`scripts/divergence_study.py`, data `docs/assets/divergence_*.csv`)
Seed-0 headless run; at two moments the timeline is saved, then 16 copies each get one extra spike (`Brain.inject_spike`, exact: the neuron fires, resets and its spike travels as normal) and run 3 s ahead. A path has *diverged* when the two flies are more than 0.1 mm apart.

| Spike goes into… | Walking (0.5 s) | Feeding (4.0 s, shadow due at 6 s) |
|---|---|---|
| any neuron, uniformly | 0 / 16 diverged; 16 changed no other spike | 2 / 16 diverged (from 2.1 s); 0.18–0.56 mm at 3 s |
| a neuron already active | 0 / 16; 16 changed nothing | 1 / 16 (from 2.1 s); 0.22 mm |
| a sensory / drive input neuron | 0 / 16; 16 changed nothing | **4 / 16**, from **235 ms** at the earliest; up to 1.15 mm; feeding briefly interrupted; jump shifted 1–3 ms |

**What it means.** The model is strongly *stable*: in most branches, not a single other spike anywhere in the brain differed over 3 s, so the nudge simply fades. A spike matters only when the network is driven hard and the spike lands in the driven stream (sugar input during feeding). When it does cascade, it changes about 58,000 spikes, but the *path* changes little, because walking speed comes mostly from our own drive (ADR-0028).

**Consequence for the concept.** "One extra spike in a randomly chosen neuron" (CLAUDE.md Phase 5) would almost always show nothing. A proposal to aim it is in [ADR-0031](0031-proposal-aimed-free-will.md).

## Batching (`scripts/batch_cost.py`)
Per-step engine work on one timeline vs 8 in one batch, sharing one awake set (prototype of the arithmetic):

| Layout | 7,300 awake (sugar) | 43,000 awake (walking fly) |
|---|---|---|
| batch-major `[8, N]` | 8.6× one timeline (no gain) | 9.6× |
| **neuron-major `[N, 8]`** | **3.6×** | **5.7×** |

The earlier guess of about 2× was wrong. A neuron-major batched engine would make 8 futures 1.4–2.2× cheaper per future, which is worth building in Phase 5, not decisive.

## The machine's limits (`scripts/monitor_system.py`; raw logs stay private in `.private/monitoring/`)
- **Memory is the tightest resource, but it was never exhausted.** With 4 worker processes (each loads the brain), Python used up to 5.4 GB and macOS's "unused" memory fell to 0.05 GB. But swap did not grow (it stayed at about 2.0–2.1 GB in every run), and a single-process determinism gate also left "unused" at 0.06 GB. macOS keeps spare memory busy as cache, so "unused near zero" is normal. *Correction:* a first draft of this ADR said memory "ran out"; it did not. The monitor now also records macOS's own memory-pressure level (normal / warning / critical) and the percentage of memory available, which are the real signals.
- **Rule, kept as a margin of safety:** at most 3 parallel brain processes, and stop if memory pressure leaves "normal" or swap starts to grow.
- **Thermal pressure stayed nominal** throughout (up to 400% CPU for 7 minutes, and an 11-minute gate). Fan speed and temperatures need `sudo powermetrics`, which the builder does not run.
- **Background load:** macOS background services (media analysis, file-system and storage clean-up) sometimes push the load average to about 17–20 with no project process running, so timing measurements should be repeated when the machine is quiet.
- One brain process uses one core by design (ADR-0007), so parallelism comes from processes.

## Decision
Record these results; use at most 3 parallel brain processes from now on; keep `Brain.inject_spike`, `Brain.awake_neurons`, `Timeline.run_recording` and `tramlines/timeline/divergence.py` (Phase 5 will need them); monitor every long run.

## Consequences
- The free-will design must change before Phase 5 (ADR-0031).
- Prediction itself is unaffected: an untouched fork still matches perfectly (the sacred tests).
- The ghost and branch workers must share the 3-process budget, which strengthens the case for computing ahead ([ADR-0030](0030-projection-not-live.md)).

## For learners
We expected one spike to change everything, as chaos stories suggest. In this brain model, most spikes vanish without a trace; only a spike in the right place, at a busy moment, ripples outward. Measuring before building saved us from a free-will button that would have shown nothing. Chapter 24 covers divergence.
