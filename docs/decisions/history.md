# Decision history

Every choice, in the order it was made, with who made it. The ADRs hold the reasoning; this page is the timeline. New entries go at the bottom; nothing is ever removed.

**Deciders:** *Owner* = the project owner. *Delegated* = Claude, inside the remit CLAUDE.md gives it. *Owner-delegated* = Claude, on a choice the owner explicitly handed over.

| # | Date | Choice | Decided by | Record |
|---|---|---|---|---|
| 1 | 2026-10-22 | The concept: a machine that predicts a fly's future | Owner | [0001](0001-concept-prediction-machine.md) |
| 2 | 2026-10-22 | Dataset FlyWire v783 | Owner | [0002](0002-dataset-flywire-v783.md) |
| 3 | 2026-10-22 | LIF neuron model of Shiu et al. 2024 | Owner | [0003](0003-neuron-model-shiu-lif.md) |
| 4 | 2026-10-22 | Python 3.12 + PyTorch | Owner | [0004](0004-python-and-pytorch.md) |
| 5 | 2026-10-22 | TypeScript viewer, FastAPI + WebSockets | Owner | [0005](0005-typescript-viewer-fastapi-websockets.md) |
| 6 | 2026-10-22 | 2D arena, no physics body | Owner | [0006](0006-2d-arena-no-physics-body.md) |
| 7 | 2026-10-22 | Determinism first | Owner | [0007](0007-determinism-first.md) |
| 8 | 2026-10-22 | Forks share weights, copy state | Owner | [0008](0008-fork-shares-weights.md) |
| 9 | 2026-10-22 | Long-term target: in the visitor's browser | Owner | [0009](0009-browser-target-phase-2.md) |
| 10 | 2026-10-22 | Honesty is a feature | Owner | [0010](0010-honesty-is-a-feature.md) |
| 11 | 2026-10-22 | The repository ships The Book | Owner | [0011](0011-the-book.md) |
| 12 | 2026-10-22 | Tooling: uv, Vite, MkDocs, pytest, ruff, mypy, git | Owner | [0012](0012-development-tooling.md) |
| 13 | 2026-10-22 | v783 files fetched from the Shiu repository, pinned | Delegated | [0013](0013-data-files-and-source.md) |
| 14 | 2026-10-22 | Challenge raised: reference code differs from CLAUDE.md 7.2 | Delegated (open) | [0014](0014-challenge-reference-model-details.md) |
| 15 | 2026-10-22 | Test conventions | Delegated | [0015](0015-test-conventions.md) |
| 16 | 2026-10-22 | Go for Phase 1 | Owner | [journal 2](../journal/2026-10-22-session-2.md) |
| 17 | 2026-10-22 | Performance machine confirmed (specs kept private) | Owner | [owner decisions](../owner-decisions.md) |
| 18 | 2026-10-22 | Neuron model verified against Brian2; refractory input discarded | Delegated | [0016](0016-verified-neuron-model.md) |
| 19 | 2026-10-22 | Annotations v2.1.0; reference neuron sets for the acceptance test | Delegated | [0017](0017-annotations-and-neuron-sets.md) |
| 20 | 2026-10-22 | Event-driven engine | Delegated | [0018](0018-event-driven-engine.md) |
| 21 | 2026-10-22 | matplotlib for figures | Delegated | [0019](0019-plotting.md) |
| 22 | 2026-10-22 | Sugar → MN9 regression bands | Delegated | [0020](0020-sugar-mn9-regression-bands.md) |
| 23 | 2026-10-22 | Go for Phase 2; push to GitHub, branch `develop` | Owner | [journal 3](../journal/2026-10-22-session-3.md) |
| 24 | 2026-10-22 | Brain state, fork, save/load | Delegated | [0021](0021-brain-state-fork-save.md) |
| 25 | 2026-10-22 | Sacred test protocol | Delegated | [0022](0022-determinism-test-protocol.md) |
| 26 | 2026-10-22 | Privacy: only the GitHub handle appears publicly; history rewritten | Owner | [journal 4](../journal/2026-10-22-session-4.md) |
| 27 | 2026-10-22 | Go for Phase 3; decisions deferred | Owner | [journal 4](../journal/2026-10-22-session-4.md) |
| 28 | 2026-10-22 | Proposals for senses and decoder | Delegated (proposals only) | [0023](0023-proposal-sensory-ports.md), [0024](0024-proposal-motor-decoder.md) |
| 29 | 2026-10-22 | World, body, 1 ms world step, timeline loop | Delegated | [0025](0025-world-and-timeline.md) |
| 30 | 2026-10-22 | Pull requests into `develop` | Owner | [0026](0026-branches-and-pull-requests.md) |
| 31 | 2026-10-22 | Sugar + bitter check run (bitter suppresses feeding) | Owner request | [0023 update](0023-proposal-sensory-ports.md) |
| 32 | 2026-10-22 | Faster engine: compute only awake neurons, bit-identical | Delegated (owner asked for speed work) | [0027](0027-awake-set-engine.md) |
| 33 | 2026-10-22 | Senses chosen: sugar, bitter, LPLC2 loom, no touch, **P9 walking drive at 100 Hz** | Owner-delegated | [0028](0028-senses-and-decoder-chosen.md) |
| 34 | 2026-10-22 | Decoder chosen: P9−MDN speed, DNa02 turning, Giant Fiber jump, MN9 feeding | Owner-delegated | [0028](0028-senses-and-decoder-chosen.md) |
| 35 | 2026-10-22 | Headless start moved 4 mm east so the path crosses food (presentation) | Owner-delegated | [0028, history step 2](0028-senses-and-decoder-chosen.md) |
| 36 | 2026-10-22 | Feeding hysteresis (start 30 Hz, stop 15 Hz) after flicker was observed | Owner-delegated | [0028, history step 3](0028-senses-and-decoder-chosen.md) |
| 37 | 2026-10-22 | Escape hop 5 → 15 mm (the 5 mm hop stayed inside the food) | Owner-delegated | [0028, history step 3](0028-senses-and-decoder-chosen.md) |
| 38 | 2026-10-22 | Body: 500 ms jump cooldown | Owner-delegated | [0028](0028-senses-and-decoder-chosen.md) |
| 39 | 2026-10-22 | Vision proposal written as a shared doc (five moves) | Owner request | [vision doc](https://claude.ai/artifact/YX2bran5jpVRDVtDFxN8Lc) |
| 40 | 2026-10-22 | Owner: "do what's best for the mission"; monitor CPU, memory, heat | Owner | [journal 6](../journal/2026-10-22-session-6.md) |
| 41 | 2026-10-22 | Divergence study run: random extra spikes almost never change the future | Owner-delegated | [0029](0029-divergence-batching-monitoring.md) |
| 42 | 2026-10-22 | Batching measured: neuron-major layout, 3.6-5.7x for 8 futures (not about 2x) | Owner-delegated | [0029](0029-divergence-batching-monitoring.md) |
| 43 | 2026-10-22 | At most 3 parallel brain processes (memory tight at 4; swap never grew) | Owner-delegated | [0029](0029-divergence-batching-monitoring.md) |
| 44 | 2026-10-22 | Projection, not live: the viewer plays timelines computed ahead | Owner-delegated | [0030](0030-projection-not-live.md) |
| 45 | 2026-10-22 | Proposed: aim the free-will spike at driven inputs, at decision moments | Proposed | [0031](0031-proposal-aimed-free-will.md) |
| 46 | 2026-10-23 | Approved: aimed free will (option 2) | Owner | [0031](0031-proposal-aimed-free-will.md) |
| 47 | 2026-10-23 | Approved: projection, not live; CLAUDE.md Phase 4, 5 and 13.3 amended to match | Owner | [0030](0030-projection-not-live.md) |
| 48 | 2026-10-23 | Patches and shadows get a strength; decision arena with laced food (0.72) and a faint shadow (0.04) | Owner-delegated | [0032](0032-decision-points.md) |
| 49 | 2026-10-23 | Free will offered at decision moments: stepping onto laced food, a shadow approaching | Owner-delegated | [0032](0032-decision-points.md) |
| 50 | 2026-10-23 | Owner: "proceed partner", taken as the Phase 3 verdict (pass, with the documented food-approach gap) and go for Phase 4 | Owner | [journal 7](../journal/2026-10-23-session-7.md) |
| 51 | 2026-10-23 | Phase 4: projector + independent ghost process + viewer; match meter compares them bit for bit | Delegated | [0033](0033-phase-4-architecture.md) |
| 52 | 2026-10-23 | Viewer fonts (Cormorant Garamond, JetBrains Mono), single dark theme, fixed meaning for each mark | Delegated | [0034](0034-viewer-design.md) |
| 53 | 2026-10-23 | FastAPI, uvicorn (locked transport) added; httpx2 for tests | Delegated | [0033](0033-phase-4-architecture.md) |
| 54 | 2026-10-23 | Owner: Phase 4 viewer watched ("spectacular"); sign-off deferred while reading | Owner | [journal 7](../journal/2026-10-23-session-7.md) |
| 55 | 2026-10-23 | Review (issue #14) accepted on points 1–3; honesty page, viewer captions and ADR-0033 corrected | Delegated (honesty, L10) | [0035](0035-proposal-honest-laplaces-demon.md) |
| 56 | 2026-10-23 | Nine review bugs fixed: connect race, stale cache key, atomic cache, crashed workers, checkpoint cleanup, freeze after jump, wall pinning, match meter counting the future, duplicate ghosts on reconnect | Delegated | issue #14 |
| 57 | 2026-10-23 | Proposed: reframe as "an honest Laplace's demon" (predictability horizon, null brain, perturbation atlas) | Proposed | [0035](0035-proposal-honest-laplaces-demon.md) |
| 58 | 2026-10-23 | Bug fixes and proposal merged; the pre-reframe project tagged **v0.4.0** ("the Devs demo") | Owner | tag `v0.4.0` |
| 59 | 2026-10-23 | **Adopted: an honest Laplace's demon.** CLAUDE.md 1.1–1.3, L1 and Phases 5–7 amended | Owner | [0035](0035-proposal-honest-laplaces-demon.md) |
| 60 | 2026-10-23 | Disjoint inputs and readouts adopted as part of the reframe; the replacement walking drive is chosen by measurement | Owner (adopted with 0035); neuron choice delegated | [0035](0035-proposal-honest-laplaces-demon.md) |
| 61 | 2026-10-23 | Issues #11–#13 closed as duplicates of #14; personal paths removed from their text | Owner | owner decisions 18 |
| 62 | 2026-10-23 | Walking drive moved upstream of P9 to CB2777 at 150 Hz (chosen by survey); speed gain 0.5 mm/s per Hz; driven and read neurons may never overlap (test) | Owner-adopted (0035), neuron choice delegated | [0036](0036-walking-drive-upstream-of-p9.md) |
| 63 | 2026-10-23 | Start moved to (−2, 6) mm because the fly now walks straight (presentation) | Delegated | [0036](0036-walking-drive-upstream-of-p9.md) |
| 64 | 2026-10-23 | Faint shadow recalibrated 0.04 → 0.055; laced food stays 0.72 | Delegated | [0036](0036-walking-drive-upstream-of-p9.md) |
| 65 | 2026-10-23 | Result 1 instruments (perturb.py, horizon study) and first-pass findings recorded | Delegated | [0037](0037-result-1-predictability-horizon.md) |
| 66 | 2026-10-23 | Heavy runs drop to 1 worker when other apps keep memory pressure at "warning" (swap grew to 2.56 GB) | Delegated | [journal 8](../journal/2026-10-23-session-8.md) |
| 67 | 2026-10-24 | Result 1 second pass: 3 seeds × 3 draws, finer edge (0.03 mV, 99.5%); the missed-spike finding holds, small voltage errors are not harmless at the laced food, and timing matters more than precision | Delegated | [0038](0038-result-1-second-pass.md) |
| 68 | 2026-10-24 | Horizon study prints progress per run; first-pass CSV labels aligned with the current code ("99.0%") | Delegated | [0038](0038-result-1-second-pass.md) |
| 69 | 2026-10-24 | Null brain: degree-preserving shuffle of receivers (weights and signs stay with senders; no self-connections or repeated pairs), plus partial rewiring | Delegated (Result 2 adopted with 0035) | [0039](0039-result-2-null-brain.md) |
| 70 | 2026-10-24 | Clamped probes added so every pathway is tested even if a brain never walks; partial-rewiring sweep added; both labelled exploratory | Delegated | [0039](0039-result-2-null-brain.md) |
| 71 | 2026-10-24 | Owner asked whether the experiment fits our expectations: predictions now written before results, and a decoder-free test added | Owner question; test delegated | [predictions](../science/null-brain-predictions.md) |
| 72 | 2026-10-24 | ADR-0036 corrected: brain "re-convergence" at the shadow was measured on spikes only, not the full state | Delegated (honesty, L10) | [0036](0036-walking-drive-upstream-of-p9.md) |
| 73 | 2026-10-24 | Proposed to the owner: a "backward horizon" (can a demon recover the past?), not yet drafted | Awaiting owner | [owner decisions](../owner-decisions.md) |
| 74 | 2026-10-24 | Bug: "one missed spike" silently did nothing when no spike was in transit (seed 0, walking). `blur` now refuses; void runs removed; ADR-0037/0038 corrected (walking: 6/6, not 9/9) | Delegated (honesty, L10) | [0038](0038-result-1-second-pass.md) |
| 75 | 2026-10-24 | Backward-horizon proposal written with a pilot (predictions first); awaiting the owner | Proposed | [0040](0040-proposal-backward-horizon.md) |
