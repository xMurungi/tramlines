"""The two brain processes behind the viewer (ADR-0033, ADR-0042).

- The **projector** computes the live timeline in 100 ms chunks and saves a
  checkpoint every simulated second.
- The **ghost** takes one checkpoint at a time, loads it on its own, and predicts
  `horizon_ms` ahead. It shares nothing with the projector but the checkpoint
  file. With the control setting it starts from the checkpoint exactly, so it is
  always right; with any other setting it first blurs the brain the way a real
  measurement could fall short (`tramlines.timeline.perturb.blur`, Result 1).
  It also computes free-will fans (ADR-XXXX): from the checkpoint behind the moment,
  it runs untouched to that moment, forks, gives each branch one aimed extra spike
  (`tramlines.timeline.branches`), and runs them all `horizon_ms` ahead.

Each runs in its own process with its own brain: two brain processes, the
machine's limit (ADR-0032). Messages go back as plain tuples on queues.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from tramlines.brain.connectome import Connectome, load_connectome
from tramlines.brain.engine import enable_determinism
from tramlines.brain.neurons import NeuronCatalog, load_catalog
from tramlines.server.fans import BRANCHES, FAN
from tramlines.server.knowledge import BY_ID
from tramlines.server.protocol import AimedSpike, FanBranch, SpikeRefused, pose_row
from tramlines.timeline import branches
from tramlines.timeline.perturb import NoSpikeInTransit, blur
from tramlines.timeline.timeline import MotorDecoder, SensoryPorts, Timeline
from tramlines.world.arena import DECISION_ARENA, DEFAULT_ARENA, Arena
from tramlines.world.decoder import FlyDecoder
from tramlines.world.fly import DEFAULT_START
from tramlines.world.senses import FlySenses

ARENAS: dict[str, Arena] = {"default": DEFAULT_ARENA, "decision": DECISION_ARENA}
CHUNK_MS = 100
CHECKPOINT_EVERY_MS = 1000

Parts = tuple[Connectome, SensoryPorts, MotorDecoder]


class Inbox(Protocol):
    def get(self) -> Any: ...


class Outbox(Protocol):
    def put(self, item: tuple[Any, ...], /) -> None: ...


def full_brain() -> Parts:
    """The whole v783 brain with the fly's senses and decoder (ADR-0028)."""
    enable_determinism()
    catalog = load_catalog()
    return load_connectome(), FlySenses.from_catalog(catalog), FlyDecoder.from_catalog(catalog)


# How each of the fly's senses is named when a spike lands in it (ADR-0028's ports).
PORT_NAMES = {
    "sugar": "sugar taste",
    "bitter": "bitter taste",
    "loom_left": "looming, left",
    "loom_right": "looming, right",
    "walk_drive": "walking drive",
}


@functools.cache
def _catalog() -> NeuronCatalog:
    return load_catalog()


def describe_input(senses: SensoryPorts, neuron: int) -> str:
    """Where a free-will spike went, in words: its sense, cell type and FlyWire root ID.

    ADR-0031: the screen must say exactly where the spike was put. Senses other than the
    fly's (the tests' probes) are named by engine index only.
    """
    if not isinstance(senses, FlySenses):
        return f"input neuron {neuron}"
    port = next((name for name in PORT_NAMES if neuron in getattr(senses, name).tolist()), "input")
    catalog = _catalog()
    root = int(catalog.root_ids[neuron])
    cell_type = "unnamed type"
    if root in catalog.annotations.index:
        cell_type = str(catalog.annotations.loc[root, "cell_type"])
    return f"{PORT_NAMES.get(port, port)} · {cell_type} · {root}"


def checkpoint_path(directory: Path, at_ms: int) -> Path:
    return directory / f"t{at_ms:07d}.pt"


def run_projector(
    out: Outbox,
    checkpoints: Path,
    arena: Arena,
    seed: int,
    duration_ms: int,
    parts: Callable[[], Parts] = full_brain,
) -> None:
    connectome, senses, decoder = parts()
    timeline = Timeline(connectome, arena, senses, decoder, seed=seed, start=DEFAULT_START)
    checkpoints.mkdir(parents=True, exist_ok=True)

    def checkpoint() -> None:
        at_ms = timeline.fly.time_ms
        timeline.save(checkpoint_path(checkpoints, at_ms))
        out.put(("checkpoint", at_ms, int(timeline.brain.state.in_flight.sum())))

    checkpoint()
    while timeline.fly.time_ms < duration_ms:
        start = timeline.fly.time_ms
        poses, spikes = timeline.run_recording(CHUNK_MS)
        fired = np.unique(spikes.neurons.numpy())
        out.put(("chunk", start, [pose_row(p) for p in poses], fired, int(spikes.neurons.numel())))
        if timeline.fly.time_ms % CHECKPOINT_EVERY_MS == 0 and timeline.fly.time_ms < duration_ms:
            checkpoint()
    out.put(("projector_done",))


def run_fan(
    timeline: Timeline,
    at_ms: int,
    horizon_ms: int,
    out: Outbox,
    describe: Callable[[int], str],
    n: int = BRANCHES,
) -> None:
    """One fan, streamed: where the spikes go, the untouched future, then each branch.

    `timeline` is the checkpoint behind `at_ms`; it is run untouched up to `at_ms` first,
    so the spikes are added exactly at the moment the viewer asked for.
    """
    timeline.run(at_ms - timeline.fly.time_ms)
    feeding_before = timeline.fly.feeding
    aim = branches.aim(timeline, n, seed=at_ms)
    aimed = [AimedSpike(neuron=k, label=describe(k)) for k, _ in aim.branches]
    refused = [
        SpikeRefused(neuron=r.neuron, label=describe(r.neuron), reason=r.reason)
        for r in aim.refused
    ]
    out.put(("fan_plan", at_ms, aim.driven, aimed, refused))
    if aim.branches:
        untouched = branches.run_untouched(timeline, horizon_ms)
        out.put(("fan_base", at_ms, [pose_row(p) for p in untouched.poses]))
        for index, (neuron, twin) in enumerate(aim.branches):
            branch = branches.run_branch(neuron, twin, untouched, horizon_ms)
            out.put(
                ("branch", fan_branch(at_ms, index, aimed[index].label, branch, feeding_before))
            )
    out.put(("fan_done", at_ms))


def fan_branch(
    at_ms: int, index: int, label: str, branch: branches.Branch, feeding_before: bool
) -> FanBranch:
    return FanBranch(
        at_ms=at_ms,
        index=index,
        neuron=branch.neuron,
        label=label,
        poses=[pose_row(p) for p in branch.poses[9::10]],
        distance_mm=branch.distance_mm[9::10],
        spike_diffs=branch.spike_diffs,
        spike_bin_ms=branches.SPIKE_BIN_MS,
        first_apart_ms=branch.first_apart_ms,
        end_distance_mm=branch.distance_mm[-1],
        max_distance_mm=max(branch.distance_mm),
        split=branch.split,
        body_rejoined=branch.body_rejoined,
        brain_rejoined=branch.brain_rejoined,
        brain_max_dv_mV=branch.brain_at_end.max_dv_mV,
        events=branches.events(branch.poses, feeding_before),
    )


def run_ghost(
    inbox: Inbox,
    out: Outbox,
    arena: Arena,
    horizon_ms: int,
    parts: Callable[[], Parts] = full_brain,
) -> None:
    """Answer each job `(knowledge, from_ms, path)` with a ghost, or a refusal saying why;
    and each fan job `(FAN, at_ms, path)` with a fan (`run_fan`).

    Checkpoints are kept, not deleted: a viewer may later ask for the same moment
    with other knowledge (ADR-0042), or for a fan.
    """
    connectome, senses, decoder = parts()
    while (job := inbox.get()) is not None:
        knowledge, from_ms, path = job
        timeline = Timeline.load(Path(path), connectome, arena, senses, decoder)
        if knowledge == FAN:
            run_fan(timeline, from_ms, horizon_ms, out, lambda k: describe_input(senses, k))
            continue
        error = BY_ID[knowledge].knowledge
        if error is not None:
            try:
                blur(timeline.brain.state, error)
            except NoSpikeInTransit as refusal:
                out.put(("refused", knowledge, from_ms, str(refusal)))
                continue
        poses = timeline.run(horizon_ms)
        out.put(("ghost", knowledge, from_ms, [pose_row(p) for p in poses]))
    out.put(("ghost_done",))
