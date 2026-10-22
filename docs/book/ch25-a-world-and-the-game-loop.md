# Chapter 25 — A 2D world and the game loop

> A brain in a jar can only think. Give it a body and a place to be, and it can *do*.

## Where we are
You have a brain you can copy perfectly. This chapter builds the world it will live in, a round dish with food in it, and the loop that every game and every robot runs: sense, decide, act, repeat. For now a few lines of ordinary code do the deciding; once the senses and the decoder are settled, the fly brain takes the wheel.

## The idea
The world is split the same way the brain was:

- **Fixed** (the `Arena`): the dish's size, where food and bitter patches are, when shadows will loom.
- **Changing** (the `FlyState`): where the fly is, which way it faces, the time, whether it is feeding.

The body is deliberately simple ([ADR-0006](../decisions/0006-2d-arena-no-physics-body.md)). It is a point with a heading. Each millisecond it receives a `MotorCommand` (how fast to walk, how fast to turn, whether to jump or stop and feed) and obeys it, except that the wall of the dish stops it.

Then the **loop**. Once per millisecond of simulated time:

1. look at the world (is the fly on food?),
2. decide what to do (here, a hand-written pilot; later, the brain),
3. move the body.

This is the "game loop" of every video game, the heartbeat that turns rules into motion. In the full machine the "decide" step runs the brain for ten of its 0.1 ms steps ([ADR-0025](../decisions/0025-world-and-timeline.md)).

## Build it
Save as `ch25/game_loop.py`:

```python
"""Chapter 25: a fly's body in a round dish, moved by a hand-written pilot."""

import math

from tramlines.world.arena import Arena, Patch
from tramlines.world.fly import FlyState, MotorCommand, step_fly

arena = Arena(radius_mm=40.0, patches=(Patch(x_mm=20.0, y_mm=0.0, radius_mm=4.0, kind="food"),))
fly = FlyState(x_mm=-20.0, y_mm=0.0, heading_rad=0.3)


def pilot(fly: FlyState, arena: Arena) -> MotorCommand:
    """Stand-in for the brain: steer towards food, stop to eat when on it."""
    if arena.patches_under(fly.x_mm, fly.y_mm):
        return MotorCommand(feed=True)
    food = arena.patches[0]
    bearing = math.atan2(food.y_mm - fly.y_mm, food.x_mm - fly.x_mm)
    error = math.remainder(bearing - fly.heading_rad, math.tau)
    return MotorCommand(forward_mm_s=15.0, turn_rad_s=3.0 * error)


for ms in range(1, 4001):  # four seconds, one millisecond at a time
    step_fly(fly, pilot(fly, arena), arena)
    if ms % 500 == 0:
        state = "feeding" if fly.feeding else "walking"
        print(f"t = {ms / 1000:.1f} s   x = {fly.x_mm:6.2f} mm   y = {fly.y_mm:5.2f} mm   {state}")
```

## Run it

```bash
uv run python ch25/game_loop.py
```

```text
t = 0.5 s   x = -12.60 mm   y =  1.10 mm   walking
t = 1.0 s   x =  -5.10 mm   y =  1.14 mm   walking
t = 1.5 s   x =   2.39 mm   y =  0.89 mm   walking
t = 2.0 s   x =   9.89 mm   y =  0.54 mm   walking
t = 2.5 s   x =  16.01 mm   y =  0.22 mm   feeding
t = 3.0 s   x =  16.01 mm   y =  0.22 mm   feeding
t = 3.5 s   x =  16.01 mm   y =  0.22 mm   feeding
t = 4.0 s   x =  16.01 mm   y =  0.22 mm   feeding
```

## The click
That fly looks purposeful. It turns towards the food, walks to it, stops and eats. Yet there is no brain in it at all: twelve lines of `pilot` did everything.

That is the uncomfortable lesson of this chapter, and the reason the next one exists. Behaviour you can see is not proof of a mind behind it. When the real brain takes over, the fly's path will come from 138,639 simulated neurons, but *also* from the choices we make about which neurons count as its eyes and tongue, and how their firing becomes steps and turns. A good simulation makes those choices visible. The project writes each one down ([ADR-0023](../decisions/0023-proposal-sensory-ports.md), [ADR-0024](../decisions/0024-proposal-motor-decoder.md)) and does not hide them behind smooth motion.

One more thing to notice: run it twice and you get the same eight lines. The world is deterministic too, and it forks with the brain. A timeline is the brain, the body and the clock together, copied as one.

## Break it

1. Set the pilot's turn gain from `3.0` to `30.0`. What happens to the path?
2. Move the food to `x_mm=45.0`, outside the dish. Where does the fly end up?
3. Make the pilot ignore the food and always return `MotorCommand(forward_mm_s=15.0, turn_rad_s=1.0)`. What shape does the fly trace?
4. Add a bitter `Patch` between the fly and the food. Change the pilot so it walks around it.

## When it goes wrong

- **The fly never stops.** It overshoots the patch between milliseconds, or the patch is too small. Print `arena.patches_under(...)` each step near the food.
- **The fly spins in place.** The turn gain is too high, or the angle error is not wrapped with `math.remainder` (so it turns the long way round).
- **Angles look wrong.** Angles are in radians, anticlockwise from the +x axis: `math.pi / 2` is "up".

## Check yourself

1. Which belongs to the fixed arena, and which to the changing fly state: the food's position, the fly's heading, the time?
2. What are the three parts of the game loop?
3. Why does a purposeful-looking path not prove there is a mind behind it?
4. What must a timeline fork copy, now that there is a world?

??? note "Answers"
    1. Food position: arena (fixed). Heading and time: fly state (changing).
    2. Sense the world, decide, act. Then repeat.
    3. Because a dozen lines of ordinary code produced one. What matters is *where* the decisions come from, which is why every brain–world mapping is documented.
    4. The brain state, the fly state, and the decoder's recent spike counts. The arena and the wiring are shared.

## Decisions in this chapter

- [ADR-0006: a 2D world, no physics body](../decisions/0006-2d-arena-no-physics-body.md)
- [ADR-0025: the world and the timeline loop](../decisions/0025-world-and-timeline.md)

## Next
The body is ready and the loop is beating; in Chapter 26 you will connect the brain's real senses and motor neurons, and see exactly where the science ends and our design begins.
