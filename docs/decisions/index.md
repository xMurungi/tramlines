# Decisions

Every decision in Tramlines is written down as an Architecture Decision Record (ADR). They are numbered from 0001, never renumbered and never deleted. Each one ends with a section *For learners*.

| # | Title | Status | Phase |
|---|---|---|---|
| [0001](0001-concept-prediction-machine.md) | The concept is a machine that predicts a fly's future | Locked | 0 |
| [0002](0002-dataset-flywire-v783.md) | The brain comes from FlyWire v783 | Locked | 0 |
| [0003](0003-neuron-model-shiu-lif.md) | Every neuron is a leaky integrate-and-fire unit, as in Shiu et al. 2024 | Locked | 0 |
| [0004](0004-python-and-pytorch.md) | Python 3.12 for the core, PyTorch for the simulation engine | Locked | 0 |
| [0005](0005-typescript-viewer-fastapi-websockets.md) | TypeScript viewer, fed by FastAPI over WebSockets | Locked | 0 |
| [0006](0006-2d-arena-no-physics-body.md) | The world is a 2D top-down arena; no physics body in v1 | Locked | 0 |
| [0007](0007-determinism-first.md) | Determinism first: CPU, float64, deterministic algorithms, seeded RNG | Locked | 0 |
| [0008](0008-fork-shares-weights.md) | A fork shares the weight matrix and copies only state | Locked | 0 |
| [0009](0009-browser-target-phase-2.md) | The long-term target is running entirely in the visitor's browser | Locked | 0 |
| [0010](0010-honesty-is-a-feature.md) | Honesty is a feature | Locked | 0 |
| [0011](0011-the-book.md) | The repository ships The Book | Locked | 0 |
| [0012](0012-development-tooling.md) | Development tooling: uv, Vite, MkDocs Material, pytest, ruff, mypy, git | Locked | 0 |
| [0013](0013-data-files-and-source.md) | The v783 files are fetched from the Shiu repository at a pinned commit | Accepted (delegated) | 0 |
| [0014](0014-challenge-reference-model-details.md) | Challenge: the reference code differs from CLAUDE.md 7.2 in five details | Challenge | 0 |
| [0015](0015-test-conventions.md) | Test conventions: data-gated tests and Book output files | Accepted (delegated) | 0 |
