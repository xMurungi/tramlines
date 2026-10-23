# 0033 — Phase 4 architecture: a projector, an independent ghost, and a viewer

- Status: Accepted (delegated)
- Date: 2026-10-23
- Phase: 4
- Decider: Claude (delegated, within locked ADR-0005 and owner-approved ADR-0030)

## Context
Phase 4 shows the live fly and its ghost on screen ([ADR-0005](0005-typescript-viewer-fastapi-websockets.md): TypeScript viewer, FastAPI + WebSockets). Under projection ([ADR-0030](0030-projection-not-live.md)) the screen plays a timeline computed ahead. The engine runs at about 0.14× real time with the walking fly, and the machine allows 2 parallel brain processes ([ADR-0032](0032-decision-points.md)).

The ghost's promise needs care. If the ghost were simply the same computed timeline drawn further ahead, its "100.000% match" would be true by construction and prove nothing.

## Options considered
1. **One timeline, drawn twice** (live and ahead). Simplest; the match meter would be meaningless.
2. **Projector + independent ghost:** the projector computes the live timeline and saves a checkpoint every second; a separate ghost process loads a checkpoint, runs 3 s ahead *on its own*, and the server compares the ghost's path with the projector's for the same seconds. Two separate computations agreeing, live, is the determinism claim shown rather than asserted.
3. **Fully live engine at 1×**: not reachable now (ADR-0027, ADR-0030).

## Decision
Option 2.

- **Projector process** (`tramlines/server/projector.py`): runs one `Timeline` (default the decision arena), streams poses and spikes in 100 ms chunks, and writes a checkpoint (`Timeline.save`) every 1 s of simulated time.
- **Ghost process** (`tramlines/server/ghost.py`): for each checkpoint, loads it and runs `H` = 3 s ahead, streaming its predicted path.
- **Match meter:** for every millisecond both have computed, the server compares the ghost's pose with the projector's, bit for bit. It shows the fraction that matched, which must read 100.000%.
- **Cache:** a finished run is kept on disk (`data/projections/`, git-ignored, rebuildable), so later viewings start instantly. The cache is only a recording of the projector's output; the ghost still recomputes independently each time it runs.
- **Server** (`tramlines/server/app.py`, FastAPI): one WebSocket, `/stream`; messages defined in `tramlines/server/protocol.py` (pydantic): `hello` (arena, neuron positions), `chunk` (poses, fired neurons), `ghost` (predicted path from a checkpoint), `match` (counts), `status` (compute frontier).
- **Viewer** (`web/`): canvas arena, the live fly in gold at the playhead, the ghost ahead (gold at low opacity, blurred), a brain panel of neuron positions lighting up as they fire, the match meter and the compute lead. The playhead waits until the lead covers the ghost's horizon.
- **Processes:** projector + ghost = 2 brain processes, the machine's limit.

## Consequences
- New Python dependencies: FastAPI, uvicorn (the locked transport, ADR-0005) and pydantic (comes with FastAPI).
- Free will (Phase 5) slots in as a third kind of worker, forking at the on-screen moment; with only 2 processes, the ghost pauses while branches compute.
- The neuron view uses soma positions from the annotations (v2.1.0), projected to 2D.

## For learners
A prediction is only impressive if it was made separately from the thing it predicts. So the ghost is computed by its own process, from a saved moment, and the screen shows how often it agreed with the live fly: every millisecond, every time. Chapters 22 and 28 build this.
