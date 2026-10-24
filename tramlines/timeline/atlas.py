"""The perturbation atlas: does one extra spike change what the fly does? (Result 3)

CLAUDE.md Phase 5, Result 3 (ADR-0035): sweep single extra spikes across neurons and
moments, screened cheaply at the spike level, with behaviour simulated only where it
might change. These are the instruments; the studies live in `scripts/`.

- `screen`: one extra spike in one neuron, then a short window: did any other spike
  change? Cheap, and most extra spikes die here.
- `outcome`: the same extra spike followed for seconds: did the fly's path or its
  behaviour (feeding, jumping) change?

An extra spike the engine refuses (a refractory neuron, or one that fired at that very
step, ADR-0041) is reported as not made, never silently treated as harmless.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import torch

from tramlines.brain.engine import SpikeRecord
from tramlines.timeline.divergence import first_divergence_ms, path_distance_mm
from tramlines.timeline.timeline import Pose, Timeline

# Two behaviours count as the same if their events match in kind and order, each
# within this many milliseconds (a jump 3 ms later is the same jump).
EVENT_TOLERANCE_MS = 50
# Result 1's test for a path that has gone wrong (ADR-0037).
PATH_EPSILON_MM = 0.1


@dataclass(frozen=True)
class Event:
    kind: str  # "feed", "stop" or "jump"
    time_ms: int


def behaviour_events(poses: Sequence[Pose]) -> list[Event]:
    """What the fly did: when it started and stopped feeding, and when it jumped."""
    out: list[Event] = []
    feeding = poses[0].feeding if poses else False
    for p in poses:
        if p.jumped:
            out.append(Event("jump", p.time_ms))
        if p.feeding != feeding:
            out.append(Event("feed" if p.feeding else "stop", p.time_ms))
            feeding = p.feeding
    return out


def behaviour_differs(
    a: Sequence[Event], b: Sequence[Event], tolerance_ms: int = EVENT_TOLERANCE_MS
) -> bool:
    if len(a) != len(b):
        return True
    return any(x.kind != y.kind or abs(x.time_ms - y.time_ms) > tolerance_ms
               for x, y in zip(a, b, strict=True))  # fmt: skip


def spike_keys(record: SpikeRecord, n_neurons: int) -> set[int]:
    return set((record.steps * n_neurons + record.neurons).tolist())


@dataclass(frozen=True)
class Screen:
    made: bool
    why_not: str  # the engine's reason, if the extra spike could not be made
    spike_differences: int  # spikes in one raster but not the other, in the window
    first_difference_ms: int | None  # after the extra spike


def screen(base: Timeline, neuron: int, truth_keys: set[int], window_ms: int) -> Screen:
    """One extra spike in `neuron` at `base`'s moment, followed for `window_ms`.

    `truth_keys` are the spikes of `base` run `window_ms` with nothing added
    (`spike_keys(base.fork().run_recording(window_ms)[1], n)`). `base` is not changed.
    """
    branch = base.fork()
    try:
        branch.brain.inject_spike(neuron)
    except ValueError as reason:
        return Screen(False, str(reason), 0, None)
    start_step = branch.brain.state.step
    n = branch.brain.connectome.n_neurons
    _, record = branch.run_recording(window_ms)
    only = spike_keys(record, n) ^ truth_keys
    first = (min(k // n for k in only) - start_step) // 10 if only else None
    return Screen(True, "", len(only), first)


@dataclass(frozen=True)
class Outcome:
    made: bool
    why_not: str
    path_wrong_from_ms: int | None  # first ms the paths are more than 0.1 mm apart
    behaviour_differs: bool
    events: tuple[Event, ...]


def outcome(base: Timeline, neuron: int, truth_poses: Sequence[Pose], horizon_ms: int) -> Outcome:
    """The extra spike followed for `horizon_ms`, against the untouched run's poses."""
    branch = base.fork()
    try:
        branch.brain.inject_spike(neuron)
    except ValueError as reason:
        return Outcome(False, str(reason), None, False, ())
    poses = branch.run(horizon_ms)
    events = behaviour_events(poses)
    return Outcome(
        made=True,
        why_not="",
        path_wrong_from_ms=first_divergence_ms(
            path_distance_mm(poses, truth_poses), PATH_EPSILON_MM
        ),
        behaviour_differs=behaviour_differs(events, behaviour_events(truth_poses)),
        events=tuple(events),
    )


def awake_neurons(base: Timeline) -> torch.Tensor:
    """Neurons not exactly at rest right now: the ones most likely to pass a spike on."""
    s = base.brain.state
    return torch.nonzero((s.v_mV != base.brain.params.v_rest_mV) | (s.g_mV != 0.0)).flatten()
