# 0009 — The long-term target is running entirely in the visitor's browser

- Status: Locked
- Date: 2026-10-22
- Phase: 0
- Decider: Owner

## Context
CLAUDE.md calls this the "Phase 2 target" in the locked table, meaning the second stage of the product after the server-backed version. In the roadmap it is Phase 7. A video of the fly is a recording; a link where the fly runs on your own machine is an experience.

## Options considered
1. **Run the engine in the browser** (WebGPU compute, or JS/WASM fallback), served as static files. No server cost, infinitely shareable.
2. **Hosted server streaming to viewers.** Simpler, but costs money per viewer, limits concurrency, and the link dies when the server does.

## Decision
After the server-backed version works (roadmap Phase 7), the full experience moves into the visitor's browser with no server.

## Consequences
- Early choices should not lock us into Python-only data formats; a compact binary CSR export is planned.
- The browser engine will use float32 and so cannot be bit-exact with the Python engine; determinism *within* the browser engine is still required (to be recorded in a Phase 7 ADR).

## For learners
"A link beats a video." If the brain runs on the visitor's own computer, anyone can press free will themselves, and nobody has to pay for a server. Chapter 30 shows how.
