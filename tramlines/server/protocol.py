"""Messages from the server to the viewer, one JSON object each (ADR-0033).

Poses travel as compact rows `[time_ms, x_mm, y_mm, heading_rad, feeding, jumped]`;
neuron indices as base64 little-endian uint32 arrays. Both keep messages small
enough to stream a whole brain's activity.
"""

from __future__ import annotations

import base64
from typing import Literal

import numpy as np
from pydantic import BaseModel

from tramlines.timeline.timeline import Pose
from tramlines.world.arena import Arena

PoseRow = tuple[int, float, float, float, bool, bool]


def pose_row(p: Pose) -> PoseRow:
    return (p.time_ms, p.x_mm, p.y_mm, p.heading_rad, p.feeding, p.jumped)


def encode_indices(indices: np.ndarray) -> str:
    return base64.b64encode(indices.astype("<u4").tobytes()).decode()


def decode_indices(text: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(text), dtype="<u4")


class PatchInfo(BaseModel):
    x_mm: float
    y_mm: float
    radius_mm: float
    kind: str
    strength: float


class LoomInfo(BaseModel):
    start_ms: int
    duration_ms: int
    direction_rad: float
    strength: float


class Hello(BaseModel):
    type: Literal["hello"] = "hello"
    arena_name: str
    radius_mm: float
    patches: list[PatchInfo]
    looms: list[LoomInfo]
    seed: int
    horizon_ms: int  # how far ahead the ghost predicts
    duration_ms: int  # how long the run is
    n_neurons: int
    neuron_xy: str  # base64 uint16 pairs (x, y), frontal view, scaled to 0..65535

    @classmethod
    def describe(
        cls, name: str, arena: Arena, seed: int, horizon_ms: int, duration_ms: int, xy: np.ndarray
    ) -> Hello:
        return cls(
            arena_name=name,
            radius_mm=arena.radius_mm,
            patches=[PatchInfo(**vars(p)) for p in arena.patches],
            looms=[LoomInfo(**vars(loom)) for loom in arena.looms],
            seed=seed,
            horizon_ms=horizon_ms,
            duration_ms=duration_ms,
            n_neurons=len(xy),
            neuron_xy=base64.b64encode(xy.astype("<u2").tobytes()).decode(),
        )


class Chunk(BaseModel):
    """100 ms of the live timeline, computed by the projector."""

    type: Literal["chunk"] = "chunk"
    t0_ms: int
    poses: list[PoseRow]
    fired: str  # base64 uint32: neurons that fired at least once in this chunk
    spikes: int  # total spikes in this chunk


class Ghost(BaseModel):
    """A prediction made independently from a checkpoint (every 10th pose, to stay small)."""

    type: Literal["ghost"] = "ghost"
    from_ms: int
    poses: list[PoseRow]


class Match(BaseModel):
    """How many milliseconds the ghost predicted, and how many matched bit for bit."""

    type: Literal["match"] = "match"
    compared_ms: int
    matched_ms: int
    by_second: list[tuple[int, int, int]] = []  # (second, compared, matched), for the playhead


class Status(BaseModel):
    type: Literal["status"] = "status"
    frontier_ms: int  # the projector has computed this far
    ghost_checkpoint_ms: int | None  # the latest moment the ghost predicted from
    computing: bool
    cached: bool  # the live timeline was replayed from disk
    error: str | None = None  # a worker stopped unexpectedly (issue #14, B4)
