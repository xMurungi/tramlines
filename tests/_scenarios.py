"""Shared set-ups for the determinism tests and their separate-process child.

A scenario is a brain plus an input schedule. The input rates change every 10 ms,
the way the world will drive them in Phase 3, so a fork taken mid-run has to
carry the schedule's effects with it.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

import numpy as np
import torch

from tramlines.brain.connectome import Connectome, from_arrays
from tramlines.brain.data import DATA_DIR
from tramlines.brain.engine import Brain, SpikeRecord
from tramlines.brain.neurons import ANNOTATIONS_FILE, REFERENCE_SUGAR_GRNS, load_catalog

SCHEDULE_HZ = (200.0, 0.0, 80.0, 150.0, 30.0)  # cycled, one entry per 10 ms
SCHEDULE_STEPS = 100
HAVE_DATA = (DATA_DIR / ANNOTATIONS_FILE).exists()


@dataclass(frozen=True)
class Scenario:
    name: str
    connectome: Connectome
    inputs: torch.Tensor
    total_steps: int

    def fork_step(self, seed: int) -> int:
        """A different, awkward fork point per seed (not a multiple of the schedule)."""
        return self.total_steps // 3 + 37 * seed

    def brain(self, seed: int) -> Brain:
        return Brain(self.connectome, self.inputs, seed=seed)


def run(brain: Brain, until_step: int) -> SpikeRecord:
    """Run to an absolute step, applying the input schedule on the way."""
    steps: list[torch.Tensor] = []
    neurons: list[torch.Tensor] = []
    while brain.state.step < until_step:
        phase = brain.state.step // SCHEDULE_STEPS
        brain.set_input_rates(SCHEDULE_HZ[phase % len(SCHEDULE_HZ)])
        chunk_end = min(until_step, (phase + 1) * SCHEDULE_STEPS)
        start = brain.state.step
        record = brain.run(chunk_end - start)
        steps.append(record.steps + start)
        neurons.append(record.neurons)
    return SpikeRecord(steps=torch.cat(steps), neurons=torch.cat(neurons))


@cache
def small() -> Scenario:
    """400 neurons, random signed wiring, 20 Poisson inputs: busy, cheap, no data needed."""
    rng = np.random.default_rng(783)
    n = 400
    pre, post = rng.integers(0, n, 8000), rng.integers(0, n, 8000)
    pairs = np.unique(np.stack([pre[pre != post], post[pre != post]], 1), axis=0)
    signed = rng.integers(1, 30, len(pairs)) * np.where(rng.random(len(pairs)) < 0.7, 1, -1)
    connectome = from_arrays(n, pairs[:, 0], pairs[:, 1], signed)
    inputs = torch.from_numpy(np.sort(rng.choice(n, 20, replace=False)))
    return Scenario("small", connectome, inputs, total_steps=3000)


@cache
def full() -> Scenario:
    """The whole v783 brain with sugar input, 100 ms."""
    from tramlines.brain.connectome import load_connectome

    inputs = load_catalog().index_of(REFERENCE_SUGAR_GRNS)
    return Scenario("full", load_connectome(), inputs, total_steps=1000)


def by_name(name: str) -> Scenario:
    return small() if name == "small" else full()
