# Roadmap

## Status

**Current phase: 0, Foundations.** Gate checks passed on 2026-10-22; waiting for the owner's "go" for Phase 1.
Waiting on owner: acknowledge ADR-0014 (Challenge); see `docs/journal/2026-10-22-session-1.md`.

## Phase 0: Foundations
- [x] Repo structure, `pyproject.toml` (uv), ruff, mypy, pytest
- [x] MkDocs Material site skeleton
- [x] Vite + TypeScript skeleton (`web/`)
- [x] ADRs 0001–0012 from the locked decisions
- [x] `scripts/fetch_data.py` downloads FlyWire v783 and verifies SHA-256
- [x] Study Eon and Shiu reference code → `docs/science/reference-model-notes.md`
- [x] **Gate:** `uv run pytest` passes; `uv run mkdocs serve` shows the site; data loads: `neurons: 138,639, connections: 15,091,983`
- [ ] Owner says "go"

## Phase 1: Hello, brain
- [ ] Choose and pin the cell type annotation source
- [ ] Verified parameter table ADR + `tramlines/brain/params.py`
- [ ] LIF engine in PyTorch: CSR weights, ring-buffer delay, Poisson input, spike recording
- [ ] Sugar → MN9 reproduction; plot in `docs/assets/`
- [ ] **Gate:** MN9 plot matches the published qualitative result; 1 s simulated, wall-clock time recorded

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
