# 0027 — Speed: compute only the awake neurons, bit for bit

- Status: Accepted (delegated; the owner asked for the speed work)
- Date: 2026-10-22
- Phase: 3 (preparing Phase 4)
- Decider: Claude (delegated)

## Context
Phase 4 needs the live fly at 1× real time or better (CLAUDE.md 13.3). The engine ran at 0.1×: 1.04 ms per 0.1 ms step with sugar input. Profiling showed half the time went on two full-brain scans per step (`nonzero` over 138,639 neurons, about 257 µs each), and most of the rest on arithmetic over all 138,639 neurons, while only **about 7,300 (5%) are ever away from rest**, even under strong sugar stimulation.

A neuron with `v` exactly at rest and `g` exactly 0 is left exactly unchanged by the update: `(0.0 · decay_v) + (0.0 · g_to_v) + V_rest = V_rest` and `0.0 · decay_g = 0.0`, in IEEE arithmetic, bit for bit. Skipping it is therefore not an approximation.

## Options considered
1. **Awake set:** keep a list of neurons not exactly at rest (plus the input neurons); compute only those; wake neurons when input reaches them; put neurons back to sleep when they are exactly at rest again. Keep spikes in flight as per-slot index lists. Results are identical to the full computation.
2. **Approximate shortcuts** (flush tiny `g` to zero, coarser time step). Faster still, but they change the model: Reserved, and they would break the Brian2 match.
3. **`torch.compile`** of the update. Measured: bit-identical, but *slower* at these sizes (45–81 µs vs 41–52 µs eager for 7,000–9,000 neurons), because the compiler's per-call overhead dominates.
4. **A compiled kernel in C++ or Numba.** Probably reaches real time, but adds a language or major dependency: Reserved for the owner.

## Decision
Option 1, in `tramlines/brain/engine.py`.

- The awake set and the in-flight index lists are **caches inside `Brain`, never part of `BrainState`**. State, fingerprints and saved files are unchanged.
- Caches are rebuilt automatically when anything outside the engine replaces or edits the state. A key of object identities plus PyTorch's per-tensor version counters detects even `state.v_mV[i] = 0`. `fork()` copies the caches instead of rebuilding them.
- Fired neurons and arrivals are kept in ascending order, so every sum happens in the same order as before.
- Data movement uses `index_select` / `index_copy_` / `index_fill_`, which are faster than general indexing and move the same bits.

## Evidence
- `tests/test_fast_engine.py` runs the previous straightforward engine (kept in `tests/_reference_engine.py`) side by side with the fast one, comparing spikes every step and the full state fingerprint at the end: small network and full brain, 3 seeds, changing inputs, a fork mid-run, and an outside edit to a sleeping neuron. Deliberately breaking the cache invalidation makes it fail at the edited step.
- The Brian2 spike-exact tests, the sugar → MN9 golden value (98) and the determinism gate all pass unchanged.

| Owner's machine, one thread | Before | After |
|---|---|---|
| Silent brain | 0.58 ms/step (0.17× real time) | **0.052 ms/step (1.9×)** |
| Sugar at 200 Hz (about 7,300 awake) | 1.04 ms/step (0.10×) | **0.22 ms/step (0.45×)** |

## Consequences
- With strong stimulation the live fly is still below 1×. What remains is mostly PyTorch's fixed cost per operation (about 2–7 µs each, a few dozen per step).
- The ghost does not need to be faster than the live fly. Starting a new ghost every second in its own worker process, with three or four running at once (the machine has the cores), keeps a 3 s horizon filled.
- How far the closed-loop fly is from 1× depends on how many neurons its senses keep awake. That will be measured in the Phase 3 headless run.
- If 1× is still not reached, the next option is a compiled kernel, which is the owner's call (`docs/owner-decisions.md`, item 4).

## For learners
Most of a brain, most of the time, is quiet. The fastest code is the code you do not run, as long as skipping it changes nothing. We proved "changes nothing" the strict way: the fast engine and the simple one run side by side and must agree on every bit, every step. Chapter 18's simple engine is still the reference.
