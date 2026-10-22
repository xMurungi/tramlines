# 0006 — The world is a 2D top-down arena; no physics body in v1

- Status: Locked
- Date: 2026-10-22
- Phase: 0
- Decider: Owner

## Context
The fly needs a body and a world for its brain to act in. Full biomechanical bodies exist (NeuroMechFly, FlyGym on MuJoCo), but FlyWire covers only the brain, not the nerve cord that drives the legs.

## Options considered
1. **2D top-down arena** with a simple kinematic fly (position, heading, speed). Enough to draw paths, which is what the concept needs.
2. **NeuroMechFly / FlyGym in MuJoCo.** Beautiful and realistic, but adds physics state to every fork, slows the loop, adds a large dependency, and the brain-to-leg mapping would be invented anyway.

## Decision
v1 uses a 2D top-down arena with simple kinematics. A 3D body is a Future Season.

## Consequences
- World state is small, so forking it is trivial and determinism is easy to keep.
- Movement comes from our motor decoder (CLAUDE.md section 8, Phase 3), which [the honesty page](../honesty.md) must explain.
- The brain does not depend on the body, so a later season can give it a new one.

## For learners
The idea we want to show is about *paths*: where the fly goes, and where its ghost says it will go. A flat map shows that perfectly. Adding legs and physics would be impressive but would not make the idea clearer, so we leave it for later. Chapter 25 builds the arena.
