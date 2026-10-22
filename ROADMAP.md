# Roadmap

## Status

**Current phase: 1, Hello, brain.** Gate checks passed on 2026-10-22; waiting for the owner's "go" for Phase 2.
Everything waiting on the owner: [`docs/owner-decisions.md`](docs/owner-decisions.md). Latest journal: `docs/journal/2026-10-22-session-2.md`.

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
- [ ] Owner says "go"

## Phase 2: The fork (determinism)
- [ ] `BrainState`, `Brain.fork()`, save/load
- [ ] Bit-exact tests (fork, cross-process, save/load), 100/100 across 10 seeds

## Phase 3: A body and a world
- [ ] Owner approves sensory ports (8.1) and motor decoder (8.2)
- [ ] Arena, kinematics, senses, decoder; determinism includes world state

## Phase 4: The ghost and the viewer
## Phase 5: Free will
## Phase 6: Polish and launch prep
## Phase 7: Into the browser
## Phase 8: Release
