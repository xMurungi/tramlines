"""The free-will fan: one moment, several futures, each one extra spike apart.

CLAUDE.md Phase 5 and ADR-0031 (aimed): every branch is a fork of the same moment
that gets exactly one extra spike (`Brain.inject_spike`), each in a different
neuron *currently receiving input*, the only place a spike is known to matter in
this model (ADR-0029, ADR-0032). The untouched fork runs beside them, and each
branch is measured against it: path distance, spike-raster differences, the first
millisecond the flies are apart, and whether the brain and the body come back.

A spike the engine refuses (a neuron refractory, or one that just fired, ADR-0041)
is reported as refused and the next candidate is tried: a branch is never a silent
copy of the untouched future.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from tramlines.brain.engine import SpikeRecord
from tramlines.timeline.divergence import (
    BrainDifference,
    brain_difference,
    first_divergence_ms,
    path_distance_mm,
    spike_differences,
)
from tramlines.timeline.timeline import Pose, Timeline

APART_MM = 0.1  # "the flies are in different places" (ADR-0029; Result 1's 0.1 mm)
BRAIN_SAME_WITHIN_MV = 1e-9  # "the brain has forgotten the spike" (Result 4's ε, ADR-0041)
SPIKE_BIN_MS = 100  # spike-raster differences counted per 100 ms (as in ADR-0029)


@dataclass(frozen=True)
class Refusal:
    """A neuron the engine would not make fire, and why."""

    neuron: int
    reason: str


@dataclass(frozen=True)
class Aim:
    """Where the extra spikes go, chosen before any future is run."""

    driven: int  # neurons receiving input at this moment: the pool spikes are drawn from
    branches: tuple[tuple[int, Timeline], ...]  # (neuron, its fork, already given the spike)
    refused: tuple[Refusal, ...]


@dataclass(frozen=True)
class Untouched:
    """The future with no extra spike: what every branch is compared with."""

    timeline: Timeline
    poses: list[Pose]
    spikes: SpikeRecord


@dataclass(frozen=True)
class Branch:
    neuron: int
    poses: list[Pose]
    distance_mm: list[float]  # from the untouched fly, every millisecond
    spike_diffs: list[int]  # spikes in one raster but not the other, per SPIKE_BIN_MS
    first_apart_ms: int | None  # ms after the spike when the flies were first > APART_MM apart
    brain_at_end: BrainDifference  # against the untouched brain, at the horizon
    same_feeding_at_end: bool  # both flies feeding, or both not, at the horizon

    @property
    def split(self) -> bool:
        """The fly went somewhere the untouched fly did not."""
        return self.first_apart_ms is not None

    @property
    def body_rejoined(self) -> bool:
        """Split, then back within APART_MM and in the same feeding state at the horizon."""
        return self.split and self.distance_mm[-1] <= APART_MM and self.same_feeding_at_end

    @property
    def brain_rejoined(self) -> bool:
        """At the horizon, measuring to BRAIN_SAME_WITHIN_MV cannot tell the brains apart."""
        return self.brain_at_end.below(BRAIN_SAME_WITHIN_MV)


def driven_neurons(timeline: Timeline) -> torch.Tensor:
    """Input neurons the world is driving right now (ADR-0031's aim), in engine order."""
    rates = timeline.senses.rates_hz(timeline.fly, timeline.arena)
    return timeline.brain.input_neurons[rates > 0]


def aim(timeline: Timeline, n: int, seed: int) -> Aim:
    """Fork `n` branches and give each one extra spike in a different driven neuron.

    Candidates are tried in an order drawn from their own generator (`seed`), never
    the brain's, so choosing does not change any future. Refusals are kept.
    """
    driven = driven_neurons(timeline)
    order = torch.randperm(len(driven), generator=torch.Generator().manual_seed(seed))
    branches: list[tuple[int, Timeline]] = []
    refused: list[Refusal] = []
    for k in order.tolist():
        if len(branches) == n:
            break
        neuron = int(driven[k])
        twin = timeline.fork()
        try:
            twin.brain.inject_spike(neuron)
        except ValueError as refusal:
            refused.append(Refusal(neuron, str(refusal)))
            continue
        branches.append((neuron, twin))
    return Aim(driven=len(driven), branches=tuple(branches), refused=tuple(refused))


def run_untouched(timeline: Timeline, horizon_ms: int) -> Untouched:
    twin = timeline.fork()
    poses, spikes = twin.run_recording(horizon_ms)
    return Untouched(twin, poses, spikes)


def run_branch(neuron: int, twin: Timeline, untouched: Untouched, horizon_ms: int) -> Branch:
    """Run one branch to the horizon and measure it against the untouched future."""
    start_step = twin.brain.state.step
    poses, spikes = twin.run_recording(horizon_ms)
    distance = path_distance_mm(poses, untouched.poses)
    n_neurons = twin.brain.connectome.n_neurons
    bin_steps = twin.brain.params.steps(SPIKE_BIN_MS)

    def relative(record: SpikeRecord) -> SpikeRecord:
        return SpikeRecord(steps=record.steps - start_step, neurons=record.neurons)

    diffs = spike_differences(relative(spikes), relative(untouched.spikes), n_neurons, bin_steps)
    bins = -(-horizon_ms // SPIKE_BIN_MS)
    diffs = (diffs + [0] * bins)[:bins]
    first = first_divergence_ms(distance, APART_MM)
    return Branch(
        neuron=neuron,
        poses=poses,
        distance_mm=distance,
        spike_diffs=diffs,
        first_apart_ms=None if first is None else first + 1,
        brain_at_end=brain_difference(twin.brain, untouched.timeline.brain),
        same_feeding_at_end=poses[-1].feeding == untouched.poses[-1].feeding,
    )


def events(poses: list[Pose], feeding_before: bool) -> list[tuple[int, str]]:
    """What the fly did, in words: when it starts or stops feeding, and when it jumps."""
    out: list[tuple[int, str]] = []
    feeding = feeding_before
    for p in poses:
        if p.jumped:
            out.append((p.time_ms, "jumps"))
        if p.feeding != feeding:
            out.append((p.time_ms, "feeds" if p.feeding else "stops feeding"))
            feeding = p.feeding
    return out
