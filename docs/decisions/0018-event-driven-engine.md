# 0018 — Engine design: event-driven spike delivery

- Status: Accepted (delegated)
- Date: 2026-10-22
- Phase: 1
- Decider: Claude (delegated)

## Context
Each step, a few of the 138,639 neurons fire. Their spikes must reach their targets 18 steps later. The reference (Brian2) uses spike queues; Eon's PyTorch port multiplies a sparse matrix by the whole spike vector every step. We also need everything to be forkable state (Phase 2) and deterministic (ADR-0007).

## Options considered
1. **Sparse matrix × spike vector every step** (Eon's approach). Simple, GPU-friendly, but touches all 15 million connections every step regardless of activity.
2. **Event-driven:** store connections grouped by sender (CSR rows = presynaptic neurons) and, each step, gather only the outgoing connections of the neurons whose spikes arrive now, then add them into g with `index_add_`.
3. **A spike queue of index lists** (Brian2-like) for in-flight spikes.

## Decision
Option 2, with in-flight spikes stored as a boolean ring buffer `[18, n_neurons]` (2.5 MB). Each step reads the slot written 18 steps ago, then writes this step's spikes into it. Details:

- Connections are stored once: `row_start` (int64), `post` (int32), `weight_mV` (float64). About 180 MB, shared by all forks (ADR-0008).
- Exact integration constants are precomputed in `params.py`.
- Poisson input draws one uniform number per input neuron per step from the timeline's own `torch.Generator`, *always*, even at rate 0. The random stream then stays aligned whatever the rates are, which keeps forks and replays simple.
- Input neuron indices must be unique, so `index_add_` adds one event per neuron.

## Consequences
- Measured on the owner's machine (one thread): a silent brain costs 0.58 ms per step (5.8 s per simulated second) in fixed work on 138k-element vectors; with sugar at 200 Hz it costs 1.04 ms per step (10.4 s per simulated second), so spike delivery is a little under half. Peak memory 1.7 GB, mostly transient while loading the table.
- That is 0.1× real time. Phase 4 needs at least 1×: an options ADR will follow (owner decision 4).
- The ring buffer and `last_spike_step` are plain tensors, so Phase 2's `BrainState` copy is simple.
- Summation order is fixed (by sender index, then storage order), so results are deterministic.

## For learners
A brain is quiet most of the time: of 138,639 neurons, only a handful fire in any tenth of a millisecond. So instead of asking every connection "did your neuron fire?", we ask only the neurons that did fire, "who do you talk to?". That is what "event-driven" means. Chapter 15 introduces the storage layout; chapter 18 uses it.
