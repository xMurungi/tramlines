"""The fly's body: a point with a heading that walks, turns, jumps and stops to feed.

There is no physics, only kinematics (ADR-0006): the motor command says how fast
to go and turn, and the body obeys, except that the arena wall stops it. The fly's
state is part of what a fork copies (ADR-0008, ADR-0025).
"""

from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import astuple, dataclass, replace

from tramlines.world.arena import Arena

WORLD_STEP_MS = 1  # the world moves once per millisecond of simulated time (ADR-0025)


@dataclass(frozen=True)
class MotorCommand:
    """What the brain asks the body to do for the next millisecond."""

    forward_mm_s: float = 0.0  # negative walks backwards
    turn_rad_s: float = 0.0  # positive turns anticlockwise (to the fly's left)
    jump_mm: float = 0.0  # an instant hop this far...
    jump_direction_rad: float = 0.0  # ...in this direction relative to the heading
    feed: bool = False  # stop and extend the proboscis


@dataclass
class FlyState:
    time_ms: int = 0
    x_mm: float = 0.0
    y_mm: float = 0.0
    heading_rad: float = 0.0
    feeding: bool = False

    def clone(self) -> FlyState:
        return replace(self)

    def fingerprint(self) -> str:
        return hashlib.sha256(struct.pack("<qddd?", *astuple(self))).hexdigest()


def step_fly(fly: FlyState, command: MotorCommand, arena: Arena) -> None:
    """Move the fly by one world step. Pure arithmetic: same inputs, same result."""
    dt_s = WORLD_STEP_MS / 1000.0
    fly.time_ms += WORLD_STEP_MS
    fly.feeding = command.feed
    if command.feed:
        return  # a feeding fly stands still
    fly.heading_rad = math.remainder(fly.heading_rad + command.turn_rad_s * dt_s, math.tau)
    distance = command.forward_mm_s * dt_s
    x = fly.x_mm + distance * math.cos(fly.heading_rad)
    y = fly.y_mm + distance * math.sin(fly.heading_rad)
    if command.jump_mm:
        direction = fly.heading_rad + command.jump_direction_rad
        x += command.jump_mm * math.cos(direction)
        y += command.jump_mm * math.sin(direction)
    fly.x_mm, fly.y_mm = _inside(x, y, arena.radius_mm)


def _inside(x_mm: float, y_mm: float, radius_mm: float) -> tuple[float, float]:
    """The wall: a fly that would leave the dish stops at its edge."""
    r = math.hypot(x_mm, y_mm)
    if r <= radius_mm:
        return x_mm, y_mm
    return x_mm * radius_mm / r, y_mm * radius_mm / r
