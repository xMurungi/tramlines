# 0005 — The Phase 1 viewer is TypeScript in the browser, fed by FastAPI over WebSockets

- Status: Locked
- Date: 2026-10-22
- Phase: 0
- Decider: Owner

## Context
The live fly, the ghost and the fan must be seen by people, ideally by sending a link. The simulation runs in Python. Something must carry a continuous stream of poses and spikes from Python to a screen.

## Options considered
1. **Browser viewer in TypeScript; FastAPI + WebSockets server.** Shareable, visual, standard, a clean path to the in-browser Phase 7.
2. **Python desktop GUI** (Qt, pygame). Simple to wire up, but not shareable and a dead end for Phase 7.
3. **Notebook widgets.** Good for experiments, poor for the cinematic screen in CLAUDE.md section 9.

## Decision
The viewer is a TypeScript web app; the server is FastAPI streaming over WebSockets.

## Consequences
- The brain and the screen are separate programs talking through a message protocol (`tramlines/server/protocol.py`, Phase 4).
- The Book gains a web part (chapters 27–29).
- The viewer stays a thin renderer, which keeps Phase 7 (moving the engine into the browser) possible.

## For learners
Your simulation and your screen do not have to be the same program. Here, Python does the thinking and a web page does the drawing, and a WebSocket is the wire between them, like a phone line that stays open. Chapter 28 builds that wire.
