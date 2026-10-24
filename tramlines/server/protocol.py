"""Messages between the server and the viewer, one JSON object each (ADR-0033, ADR-0042).

The server sends everything below except `Choose`, the one message a viewer sends:
which knowledge setting it wants to watch. Ghosts, matches and refusals carry the
setting they belong to, so a viewer can switch between settings already computed.

Poses travel as compact rows `[time_ms, x_mm, y_mm, heading_rad, feeding, jumped]`;
neuron indices as base64 little-endian uint32 arrays. Both keep messages small
enough to stream a whole brain's activity.
"""

from __future__ import annotations

import base64
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field, field_validator

from tramlines.server.knowledge import BY_ID, CONTROL, RIGHT_WITHIN_MM, SETTINGS
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


class Result1Count(BaseModel):
    """Result 1's evidence for one stop (owner decision 24): right for 3 s, of all made."""

    moment: str
    right: int
    total: int


class KnowledgeOption(BaseModel):
    """One stop of the knowledge slider, in slider order."""

    id: str
    label: str
    description: str
    needs_spike_in_transit: bool
    result1: list[Result1Count] = Field(default_factory=list)


def knowledge_options() -> list[KnowledgeOption]:
    return [
        KnowledgeOption(
            id=s.id,
            label=s.label,
            description=s.description,
            needs_spike_in_transit=s.needs_spike_in_transit,
            result1=[
                Result1Count(moment=e.moment, right=e.right, total=e.total) for e in s.evidence
            ],
        )
        for s in SETTINGS
    ]


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
    knowledge: list[KnowledgeOption] = Field(default_factory=knowledge_options)
    right_within_mm: float = RIGHT_WITHIN_MM  # "on path" for an imperfect ghost (Result 1)

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


class Checkpoint(BaseModel):
    """A saved moment of the live timeline, which every ghost starts from."""

    type: Literal["checkpoint"] = "checkpoint"
    at_ms: int
    in_flight: int  # spikes in transit: with none, "one missed spike" has nothing to miss


class Ghost(BaseModel):
    """A prediction made independently from a checkpoint (every 10th pose, to stay small)."""

    type: Literal["ghost"] = "ghost"
    knowledge: str = CONTROL
    from_ms: int
    poses: list[PoseRow]


class Refused(BaseModel):
    """A ghost that could not be made, and why. Never replaced by a silent perfect copy."""

    type: Literal["refused"] = "refused"
    knowledge: str
    from_ms: int
    reason: str


class Match(BaseModel):
    """How the ghosts of one knowledge setting compared with the live fly.

    `matched_ms` counts milliseconds equal bit for bit (the control's test, ADR-0033);
    `close_ms` counts those within `RIGHT_WITHIN_MM` (Result 1's test, ADR-0037).
    """

    type: Literal["match"] = "match"
    knowledge: str = CONTROL
    compared_ms: int
    matched_ms: int
    close_ms: int = 0
    # (second, compared, matched, close), so a viewer counts only what it has played (#14, B7).
    by_second: list[tuple[int, int, int, int]] = []
    # (from_ms, ms the ghost stayed within RIGHT_WITHIN_MM), once its whole horizon is checked.
    right_for: list[tuple[int, int]] = []


class Status(BaseModel):
    type: Literal["status"] = "status"
    frontier_ms: int  # the projector has computed this far
    ghost_checkpoint_ms: int | None  # the latest moment the ghost predicted from
    computing: bool
    cached: bool  # the live timeline was replayed from disk
    error: str | None = None  # a worker stopped unexpectedly (issue #14, B4)
    to_compute: dict[str, int] = {}  # chosen setting -> ghosts still to compute for it


class Choose(BaseModel):
    """Viewer → server: show me the ghost with this much knowledge, from about this moment."""

    type: Literal["choose"] = "choose"
    knowledge: str
    from_ms: int = Field(default=0, ge=0)  # the viewer's playhead: compute from here first

    @field_validator("knowledge")
    @classmethod
    def known(cls, value: str) -> str:
        if value not in BY_ID:
            raise ValueError(f"unknown knowledge setting: {value!r}")
        return value
