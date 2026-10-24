# Roadmap

## Status

**Current phase: 5, The demon's limits** (reframed 2026-10-23, ADR-0035; the pre-reframe project is tag `v0.4.0`). Phase 4's viewer is built and watched; its formal sign-off is pending.
Everything waiting on the owner: [`docs/owner-decisions.md`](docs/owner-decisions.md). Latest journal: `docs/journal/2026-10-24-session-9.md`. Next: Result 3, the perturbation atlas (pre-register it as Result 4 was). What remains: `docs/remaining-and-suggestions.md`.

## Phase 0: Foundations
- [x] Repo structure, `pyproject.toml` (uv), ruff, mypy, pytest
- [x] MkDocs Material site skeleton
- [x] Vite + TypeScript skeleton (`web/`)
- [x] ADRs 0001–0012 from the locked decisions
- [x] `scripts/fetch_data.py` downloads FlyWire v783 and verifies SHA-256
- [x] Study Eon and Shiu reference code → `docs/science/reference-model-notes.md`
- [x] **Gate:** `uv run pytest` passes; `uv run mkdocs serve` shows the site; data loads: `neurons: 138,639, connections: 15,091,983`
- [x] Owner says "go" (2026-10-22)

## Phase 1: Hello, brain
- [x] Choose and pin the cell type annotation source (ADR-0017)
- [x] Verified parameter table ADR + `tramlines/brain/params.py` (ADR-0016)
- [x] LIF engine in PyTorch: CSR weights, ring-buffer delay, Poisson input, spike recording (ADR-0018)
- [x] Engine matches Brian2 spike for spike on golden networks
- [x] Sugar → MN9 reproduction; plot in `docs/assets/` (ADR-0020); cross-checked against Brian2 on v783
- [x] Book chapters 17 and 18
- [x] **Gate:** MN9 plot matches the published qualitative result; 1 s simulated in 10.4 s wall-clock on the owner's machine
- [x] Owner says "go" (2026-10-22)

## Phase 2: The fork (determinism)
- [x] `BrainState`, `Brain.fork()`, save/load (ADR-0021)
- [x] Bit-exact tests (fork, cross-process, save/load), 100/100 across 10 seeds (ADR-0022)
- [x] Book chapters 19, 20, 21
- [x] Owner says "go" (2026-10-22)

## Phase 3: A body and a world
- [x] Proposal ADRs for sensory ports (0023) and motor decoder (0024), with a measured survey
- [x] Sensory ports (8.1) and motor decoder (8.2): delegated by the owner, chosen in ADR-0028
- [x] Arena, fly kinematics, timeline loop (ADR-0025)
- [x] Determinism tests include world state (timeline fork / fresh process / save-load)
- [x] Book chapter 25
- [x] `tramlines/world/senses.py` and `decoder.py`; Book chapter 26; honesty page updated
- [x] Engine speed-up, bit-identical (ADR-0027)
- [x] **Gate run:** `docs/assets/headless_seed0.png`: walks, feeds on food, escapes the shadow (it does not *approach* food: no distant food sense in the model); determinism 100%
- [x] Decision points in the arena (ADR-0032)
- [x] Owner's verdict on the gate; "go" for Phase 4 ("proceed partner", 2026-10-23)

## Phase 4: The ghost and the viewer
- [x] Architecture: projector + independent ghost + viewer (ADR-0033); look (ADR-0034)
- [x] `tramlines/server/` (FastAPI, WebSocket, cached runs) and the `web/` viewer
- [x] Match meter: 100.000% at first light (24,000 ms checked)
- [x] Book chapter 22
- [x] 60 s gate run precomputed: 60 ghost predictions, 177,000/177,000 ms matched
- [ ] Book chapters 27, 28, 29
- [ ] **Gate:** owner watches the ghost lead and the fly follow, perfectly, for 60 s
## Phase 5: The demon's limits, and free will (ADR-0035)
- [x] Disjoint inputs and readouts, with a test: walking drive moved upstream of P9 (ADR-0036)
- [x] Result 1, first pass: predictability horizon (ADR-0037)
- [x] Result 1, second pass: 3 seeds × 3 draws; what the ghost must know depends on when it looks (ADR-0038)
- [x] Result 2: null brain (degree-preserving shuffle), partial rewiring and a decoder-free check (ADR-0039)
- [ ] Result 3: perturbation atlas + decoder robustness
- [x] Result 4: the backward horizon, pre-registered (ADR-0040, ADR-0041)
- [ ] Viewer: knowledge slider; control ghost labelled; the aimed free-will fan
- [ ] **Gate:** a stranger understands it in 30 s
## Phase 6: Polish and launch prep
## Phase 7: Into the browser
## Phase 8: Release
