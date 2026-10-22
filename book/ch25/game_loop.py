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
