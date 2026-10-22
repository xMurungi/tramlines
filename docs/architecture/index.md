# Architecture

Phase 0: the shape the code will grow into. Each box is filled in by the phase named beside it.

```mermaid
flowchart LR
  data[(FlyWire v783 files)] --> load[brain/data.py<br/>Phase 0]
  load --> engine[brain/engine.py<br/>LIF in PyTorch, Phase 1]
  engine --> state[brain/state.py<br/>fork and save, Phase 2]
  world[world/<br/>arena, senses, decoder, Phase 3] <--> engine
  state --> timeline[timeline/<br/>ghost and branches, Phases 4-5]
  timeline --> server[server/<br/>FastAPI + WebSocket, Phase 4]
  server --> web[web/<br/>TypeScript viewer, Phase 4]
```

*Diagram: the data files feed the loader, the loader feeds the engine, the engine exchanges senses and movement with the world, timelines fork the engine's state, and the server streams timelines to the web viewer.*

The brain and the world are separate packages, so the brain never knows what body it drives ([ADR-0006](../decisions/0006-2d-arena-no-physics-body.md)). Forks share weights and copy state ([ADR-0008](../decisions/0008-fork-shares-weights.md)).
