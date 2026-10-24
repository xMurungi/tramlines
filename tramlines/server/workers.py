"""The two brain processes behind the viewer (ADR-0033, ADR-0042).

- The **projector** computes the live timeline in 100 ms chunks and saves a
  checkpoint every simulated second.
- The **ghost** takes one checkpoint at a time, loads it on its own, and predicts
  `horizon_ms` ahead. It shares nothing with the projector but the checkpoint
  file. With the control setting it starts from the checkpoint exactly, so it is
  always right; with any other setting it first blurs the brain the way a real
  measurement could fall short (`tramlines.timeline.perturb.blur`, Result 1).

Each runs in its own process with its own brain: two brain processes, the
machine's limit (ADR-0032). Messages go back as plain tuples on queues.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from tramlines.brain.connectome import Connectome, load_connectome
from tramlines.brain.engine import enable_determinism
from tramlines.brain.neurons import load_catalog
from tramlines.server.knowledge import BY_ID
from tramlines.server.protocol import pose_row
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


def run_ghost(
    inbox: Inbox,
    out: Outbox,
    arena: Arena,
    horizon_ms: int,
    parts: Callable[[], Parts] = full_brain,
) -> None:
    """Answer each job `(knowledge, from_ms, path)` with a ghost, or a refusal saying why.

    Checkpoints are kept, not deleted: a viewer may later ask for the same moment
    with other knowledge (ADR-0042).
    """
    connectome, senses, decoder = parts()
    while (job := inbox.get()) is not None:
        knowledge, from_ms, path = job
        timeline = Timeline.load(Path(path), connectome, arena, senses, decoder)
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
