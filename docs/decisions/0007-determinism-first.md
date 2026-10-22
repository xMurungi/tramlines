# 0007 — Determinism first: CPU, float64, deterministic algorithms, seeded per-timeline RNG

- Status: Locked
- Date: 2026-10-22
- Phase: 0
- Decider: Owner

## Context
The ghost must predict the live fly perfectly. If the two copies differ by a single rounding error, their spikes will eventually differ, and the illusion breaks on screen. GPUs and multithreaded sums can add numbers in a different order each run, which changes the last bits of the result.

## Options considered
1. **Determinism first**: CPU, float64, `torch.use_deterministic_algorithms(True)`, fixed thread count, one seeded `torch.Generator` per timeline. Move to GPU only after the bit-exact tests pass.
2. **Performance first on GPU**, tolerating small drift and resynchronising the ghost. Faster, but the "always right" promise becomes "mostly right".

## Decision
Until the bit-exact prediction test passes, everything runs on CPU in float64 with deterministic algorithms and a seeded generator per timeline.

## Consequences
- The sacred tests (`tests/test_determinism.py`, Phase 2) become the project's backbone.
- CPU float64 is slower; the performance budget (CLAUDE.md 13.3) must be measured and may need ADRs.
- Random numbers must never come from a global source; every timeline carries its own.

## For learners
A computer is deterministic: give it the same starting point and the same instructions and it does exactly the same thing. But "the same" has to mean *bit for bit*. Adding numbers in a different order can change the last decimal place, and in a brain that tiny change can grow into a different spike. Chapter 12 shows this with seeds; chapter 21 tests it at scale.
