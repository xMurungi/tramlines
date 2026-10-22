"""The 2D arena: a round dish seen from above, with food, bitter patches and looming shadows.

Everything here is fixed for the arena's life and shared by every fork (ADR-0025).
Units: millimetres, radians, milliseconds of simulated time. Angles are measured
anticlockwise from the +x axis.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

PatchKind = Literal["food", "bitter"]


@dataclass(frozen=True)
class Patch:
    x_mm: float
    y_mm: float
    radius_mm: float
    kind: PatchKind

    def contains(self, x_mm: float, y_mm: float) -> bool:
        return math.hypot(x_mm - self.x_mm, y_mm - self.y_mm) <= self.radius_mm


@dataclass(frozen=True)
class Loom:
    """A shadow approaching the fly from one direction, growing over `duration_ms`."""

    start_ms: int
    duration_ms: int
    direction_rad: float  # where it comes from, in arena coordinates

    def progress(self, time_ms: int) -> float:
        """0 before it starts, rising to 1 as it arrives, 0 again after."""
        elapsed = time_ms - self.start_ms
        if elapsed < 0 or elapsed >= self.duration_ms:
            return 0.0
        return (elapsed + 1) / self.duration_ms


@dataclass(frozen=True)
class Arena:
    radius_mm: float = 40.0
    patches: tuple[Patch, ...] = field(default_factory=tuple)
    looms: tuple[Loom, ...] = field(default_factory=tuple)

    def patches_under(self, x_mm: float, y_mm: float) -> tuple[Patch, ...]:
        return tuple(p for p in self.patches if p.contains(x_mm, y_mm))

    def active_loom(self, time_ms: int) -> tuple[Loom, float] | None:
        for loom in self.looms:
            progress = loom.progress(time_ms)
            if progress > 0.0:
                return loom, progress
        return None


# A first layout for headless runs and the Phase 3 gate; a presentation choice (ADR-0025).
# With DEFAULT_START (fly.py) the fly's path crosses the food (ADR-0028).
DEFAULT_ARENA = Arena(
    radius_mm=40.0,
    patches=(
        Patch(x_mm=18.0, y_mm=6.0, radius_mm=5.0, kind="food"),
        Patch(x_mm=-14.0, y_mm=-16.0, radius_mm=5.0, kind="bitter"),
    ),
    looms=(Loom(start_ms=6_000, duration_ms=500, direction_rad=math.pi / 2),),
)
