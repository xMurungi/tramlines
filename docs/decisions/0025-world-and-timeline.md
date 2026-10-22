# 0025 — The world, the fly's body, and the timeline loop

- Status: Accepted (delegated)
- Date: 2026-10-22
- Phase: 3
- Decider: Claude (delegated). Which neurons are senses and readouts, and how rates become movement, are *not* decided here ([ADR-0023](0023-proposal-sensory-ports.md), [ADR-0024](0024-proposal-motor-decoder.md), awaiting the owner).

## Context
Phase 3 gives the brain a body and a world ([ADR-0006](0006-2d-arena-no-physics-body.md): 2D, top-down, no physics). CLAUDE.md 8.3 fixes the loop's shape and says the world updates every 1 ms of simulated time (10 brain steps), recorded as an ADR. Everything the world adds must fork with the brain and stay bit-exact.

## Options considered
1. **Separate immutable arena + small mutable fly state + a `Timeline` that runs the loop; senses and decoder plug in through two small interfaces.** Lets the world be built and tested now, while the neuron choices wait for the owner.
2. **Build the world and the ports together.** Simpler on paper, but would mean implementing unapproved neuron choices.
3. **Physics engine for the body.** Ruled out by ADR-0006.

## Decision
Option 1.

- **Arena** (`tramlines/world/arena.py`, immutable, shared by forks): a round dish (default radius 40 mm), circular food and bitter patches, and looming shadows scheduled by time and direction (their size grows from 0 to 1 over their duration). The default layout is a presentation choice and may change freely.
- **Fly** (`tramlines/world/fly.py`): position, heading, time and feeding flag, in float64. Each 1 ms step applies a `MotorCommand`: forward speed (negative is backwards), turn rate, an optional instant jump, or feed (stand still). The wall stops the fly at the dish's edge.
- **Timeline** (`tramlines/timeline/timeline.py`): each millisecond, the senses set the brain's input rates from the fly and the arena; the brain runs 10 steps; readout spikes are counted into a sliding window (default 50 ms); the decoder turns the window's rates into a `MotorCommand`; the body moves.
- **What a timeline fork copies:** brain state, fly state, and the decoder's spike-count window. Everything else is shared.
- **Interfaces** `SensoryPorts` (input neurons + `rates_hz(fly, arena)`) and `MotorDecoder` (readout neurons + window + `command(rates, fly)`) must be pure functions.
- **Timeline save/load** writes brain state, fly state and window in one file, checked against the wiring, parameters and input neurons.

## Consequences
- The sacred tests now cover whole timelines, driven by clearly labelled *test-only* probe senses and decoder in `tests/_scenarios.py`. In every one, the fly walks off a food patch, so the world really changes the brain's input mid-run.
- Once the owner approves the ports and decoder, they slot in without changing the loop.
- The Phase 3 gate (a trajectory showing purposeful behaviour) cannot be attempted until then.
- Python overhead per world step is small next to the 10 brain steps.

## For learners
Most interactive programs are a loop: sense, think, act, repeat. Ours runs a thousand times per simulated second. Keeping the world's fixed parts (the dish, the food) apart from its changing parts (where the fly is) is the same trick as brain wiring versus brain state, and it is what makes the whole world forkable. Chapter 25 builds this loop.
