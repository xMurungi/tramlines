"""The two brain processes behind the viewer (ADR-0033).

- The **projector** computes the live timeline in 100 ms chunks and saves a
  checkpoint every simulated second.
- The **ghost** takes each checkpoint, loads it on its own, and predicts
  `horizon_ms` ahead. It shares nothing with the projector but the checkpoint
  file, so when its path equals the live one, that is two separate computations
  agreeing.

Each runs in its own process with its own brain: two brain processes, the
machine's limit (ADR-0032). Messages go back as plain tuples on queues.
"""

from __future__ import annotations

from multiprocessing.queues import Queue
from pathlib import Path
from typing import Any

import numpy as np

from tramlines.brain.connectome import load_connectome
from tramlines.brain.engine import enable_determinism
from tramlines.brain.neurons import load_catalog
from tramlines.server.protocol import pose_row
from tramlines.timeline.timeline import Timeline
from tramlines.world.arena import DECISION_ARENA, DEFAULT_ARENA, Arena
from tramlines.world.decoder import FlyDecoder
from tramlines.world.fly import DEFAULT_START
from tramlines.world.senses import FlySenses

ARENAS: dict[str, Arena] = {"default": DEFAULT_ARENA, "decision": DECISION_ARENA}
CHUNK_MS = 100
CHECKPOINT_EVERY_MS = 1000


def _parts() -> tuple[Any, FlySenses, FlyDecoder]:
    enable_determinism()
    catalog = load_catalog()
    return load_connectome(), FlySenses.from_catalog(catalog), FlyDecoder.from_catalog(catalog)


def run_projector(
    out: Queue[tuple[Any, ...]],
    checkpoints: Path,
    arena_name: str,
    seed: int,
    duration_ms: int,
) -> None:
    connectome, senses, decoder = _parts()
    arena = ARENAS[arena_name]
    timeline = Timeline(connectome, arena, senses, decoder, seed=seed, start=DEFAULT_START)
    checkpoints.mkdir(parents=True, exist_ok=True)

    def checkpoint() -> None:
        path = checkpoints / f"t{timeline.fly.time_ms:07d}.pt"
        timeline.save(path)
        out.put(("checkpoint", timeline.fly.time_ms, str(path)))

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
    inbox: Queue[tuple[int, str] | None],
    out: Queue[tuple[Any, ...]],
    arena_name: str,
    horizon_ms: int,
) -> None:
    connectome, senses, decoder = _parts()
    arena = ARENAS[arena_name]
    while (job := inbox.get()) is not None:
        from_ms, path = job
        timeline = Timeline.load(Path(path), connectome, arena, senses, decoder)
        poses = timeline.run(horizon_ms)
        out.put(("ghost", from_ms, [pose_row(p) for p in poses]))
    out.put(("ghost_done",))
