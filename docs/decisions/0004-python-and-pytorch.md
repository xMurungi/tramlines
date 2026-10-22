# 0004 — Python 3.12 for the core, PyTorch for the simulation engine

- Status: Locked
- Date: 2026-10-22
- Phase: 0
- Decider: Owner

## Context
The engine multiplies a sparse 138k × 138k matrix by a spike vector ten thousand times per simulated second, and must later run batched branches. The reference models are written in Python (Brian2, PyTorch). The Book teaches a beginner.

## Options considered
1. **Python + PyTorch.** Reuses the existing model and data tooling (pandas, parquet). Sparse tensors, deterministic-algorithm mode, explicit RNG generators, CPU and GPU from one codebase.
2. **Python + Brian2.** The exact simulator Shiu et al. used. But code generation hides the state, which makes forking and bit-exact save/restore hard.
3. **Rust or C++.** Fastest, but a much steeper Book and no shared tooling with the reference.

## Decision
Core language is Python 3.12; the simulation engine is written in PyTorch.

## Consequences
- We own every line of the step function, so every piece of state is visible and forkable.
- PyTorch's determinism switches serve [ADR-0007](0007-determinism-first.md).
- Performance on CPU float64 needs measuring in Phase 1; changing language later is Reserved.
- Python is pinned to 3.12 in `pyproject.toml` and `.python-version`.

## For learners
Python is the language; PyTorch is a toolbox inside it for doing maths on big grids of numbers quickly. We picked a language a beginner can read and a toolbox that scientists already use for exactly this model. Chapters 2 and 16 introduce each.
