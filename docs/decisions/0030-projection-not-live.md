# 0030 — The viewer shows a projection computed ahead, not a fly simulated in real time

- Status: Accepted (owner-delegated: "do what's best for the mission", 2026-10-22). Changes CLAUDE.md Phase 4's "live must run at ≥ 1× real time"; the owner can reverse it.
- Date: 2026-10-22
- Phase: 3 (decides Phase 4's design)
- Decider: Claude, on the owner's delegation

## Context
CLAUDE.md Phase 4 asks for the live fly to run at ≥ 1× real time. After the speed work ([ADR-0027](0027-awake-set-engine.md)) the closed-loop fly runs at 0.12×; reaching 1× needs a compiled kernel (a toolchain change) and still leaves no budget for the ghost and branches on a machine limited to about 3 brain processes ([ADR-0029](0029-divergence-batching-monitoring.md)).

But in a deterministic simulation a run computed ahead and a run computed "live" are **bit-identical**. That is not a workaround; it is the idea of tram lines itself.

## Options considered
1. **Projection:** compute the timeline ahead of the screen and play it at real speed; the ghost is the same timeline drawn further ahead; free will forks at the on-screen moment and the branches resolve as they finish. Nothing is faked.
2. **Real-time live simulation** (as specified): needs about 8× more speed, plus capacity for the ghost and branches.
3. **Slow the on-screen clock** (show 0.12× speed, labelled). Honest, but the fly crawls and the clip loses its pull.

## Decision
Option 1.

- A **compute worker** keeps a lead of several seconds over the screen (at 0.12×, a short preparation before the first frame, or a precomputed opening).
- The **screen plays** poses at real speed: that is the live fly. The **ghost** is the same timeline's poses further ahead, so the match meter is 100.000% by construction, and the sacred tests are what make that claim true.
- **Free will** forks at the on-screen moment; branches are computed by up to 3 workers and drawn as they resolve (faint and noisy first, sharpening to gold).
- **Replay** reloads a saved moment and plays it again.
- The honesty page says, in one sentence, that what you see was computed moments before you see it.

## Consequences
- Phase 4 no longer depends on a compiled kernel. Speed now decides only how long the opening preparation and the branch resolution take.
- The server protocol streams poses with timestamps, and shows the compute lead as well as the screen time.
- CLAUDE.md's Phase 4 text no longer matches the plan; the owner may want it updated (changing CLAUDE.md is the owner's).

## For learners
If the future is fixed, recording it and watching it live are the same thing. We use that: the machine works a few seconds ahead of what you see, like a projector running a film it is still printing. Chapter 22 builds the ghost.
