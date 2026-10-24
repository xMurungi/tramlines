# Decisions

Every decision in Tramlines is written down as an Architecture Decision Record (ADR). They are numbered from 0001, never renumbered and never deleted. Each one ends with a section *For learners*. Decisions waiting for the owner are collected on [one page](../owner-decisions.md). Every choice, in order and with who made it: [decision history](history.md).

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
| [0016](0016-verified-neuron-model.md) | The neuron model, verified against Brian2 spike for spike | Accepted (delegated) | 1 |
| [0017](0017-annotations-and-neuron-sets.md) | Annotation release v2.1.0, and the neurons of the sugar → MN9 test | Accepted (delegated) | 1 |
| [0018](0018-event-driven-engine.md) | Engine design: event-driven spike delivery | Accepted (delegated) | 1 |
| [0019](0019-plotting.md) | matplotlib for figures, in an optional dependency group | Accepted (delegated) | 1 |
| [0020](0020-sugar-mn9-regression-bands.md) | Sugar → MN9: the acceptance result and its regression bands | Accepted (delegated) | 1 |
| [0021](0021-brain-state-fork-save.md) | Brain state, forking, and saving to disk | Accepted (delegated) | 2 |
| [0022](0022-determinism-test-protocol.md) | The sacred tests: what "identical" means and how it is proved | Accepted (delegated) | 2 |
| [0023](0023-proposal-sensory-ports.md) | Proposal: which neurons are the fly's senses | Superseded by 0028 | 3 |
| [0024](0024-proposal-motor-decoder.md) | Proposal: how brain activity becomes movement | Superseded by 0028 | 3 |
| [0025](0025-world-and-timeline.md) | The world, the fly's body, and the timeline loop | Accepted (delegated) | 3 |
| [0026](0026-branches-and-pull-requests.md) | Every change arrives through a pull request into `develop` | Accepted (owner request) | 3 |
| [0027](0027-awake-set-engine.md) | Speed: compute only the awake neurons, bit for bit | Accepted (delegated) | 3 |
| [0028](0028-senses-and-decoder-chosen.md) | The fly's senses and motor decoder, as chosen | Accepted (owner delegated) | 3 |
| [0029](0029-divergence-batching-monitoring.md) | What one extra spike does, what batching saves, and the machine's limits | Accepted (owner delegated) | 3 |
| [0030](0030-projection-not-live.md) | The viewer shows a projection computed ahead, not real-time simulation | Accepted (owner approved) | 3 |
| [0031](0031-proposal-aimed-free-will.md) | Proposal: aim the free-will spike where it can matter | Accepted (owner, 2026-10-23) | 3 |
| [0032](0032-decision-points.md) | Decision points: where one spike can change what the fly does | Accepted (owner delegated) | 3 |
| [0033](0033-phase-4-architecture.md) | Phase 4 architecture: a projector, an independent ghost, and a viewer | Accepted (delegated) | 4 |
| [0034](0034-viewer-design.md) | The viewer's look: fonts, a single dark theme, and what each mark means | Accepted (delegated) | 4 |
| [0035](0035-proposal-honest-laplaces-demon.md) | An honest Laplace's demon (from the review in issue #14) | **Accepted: owner adopted** | 4 |
| [0036](0036-walking-drive-upstream-of-p9.md) | The walking drive moves upstream of P9: speed becomes the brain's answer | Accepted (with 0035) | 5 |
| [0037](0037-result-1-predictability-horizon.md) | Result 1, first pass: to foresee this brain you need its spikes, not its decimals | Accepted (delegated) | 5 |
| [0038](0038-result-1-second-pass.md) | Result 1, second pass: what the ghost must know depends on when it looks | Accepted (delegated) | 5 |
| [0039](0039-result-2-null-brain.md) | Result 2: the behaviour lives in the wiring, and survives a lot of damage to it | Accepted (delegated) | 5 |
| [0040](0040-proposal-backward-horizon.md) | Proposal: the backward horizon (can the demon recover the past?) | **Accepted: owner adopted** | 5 |
