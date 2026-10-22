# 0008 — A fork shares the weight matrix and copies only state

- Status: Locked
- Date: 2026-10-22
- Phase: 0
- Decider: Owner

## Context
The ghost and every free-will branch are copies of the running brain. The weight matrix (15 million connections) takes hundreds of megabytes. Copying it for every branch would make eight branches cost gigabytes.

## Options considered
1. **Share the immutable weights; copy only state** (voltages, conductances, refractory timers, delay buffer, RNG state, world state). A few MB per fork.
2. **Deep-copy the whole brain per fork.** Simplest code, but memory grows by hundreds of MB per branch, and copying takes seconds.

## Decision
Forks share one immutable weight matrix; a fork copies only mutable state.

## Consequences
- Weights must be truly immutable after loading. Silencing experiments that edit weights need their own copy, deliberately.
- `BrainState` (Phase 2) must contain *all* mutable state, or forks will silently share something they should not.
- Many cheap futures become possible, which the fan needs.

## For learners
A brain in this simulation has two parts: its wiring, which never changes, and its *state*, the voltages and timers that change every tenth of a millisecond. To copy a mind at one instant, you only need to copy the state; both copies can read the same wiring. Chapter 20 builds `fork()`.
