"""A timeline: one brain, one body, one clock, forkable as a single thing.

The closed loop (CLAUDE.md 8.3), once per millisecond of simulated time:

    world ──▶ senses ──▶ Poisson rates ──▶ brain (10 steps of 0.1 ms)
      ▲                                          │
      └── fly moves ◀── decoder ◀── readout spike counts (sliding window)

Which neurons are senses and readouts, and how rates become movement, are the
owner's decisions (ADR-0023, ADR-0024). This module only defines the shape of
those two pieces and runs the loop (ADR-0025).
"""

from __future__ import annotations

import hashlib
from dataclasses import astuple, dataclass
from pathlib import Path
from typing import Protocol

import torch

from tramlines.brain.connectome import Connectome
from tramlines.brain.engine import Brain
from tramlines.brain.params import PARAMS
from tramlines.brain.state import BrainState
from tramlines.world.arena import Arena
from tramlines.world.fly import WORLD_STEP_MS, FlyState, MotorCommand, step_fly

BRAIN_STEPS_PER_WORLD_STEP = PARAMS.steps(WORLD_STEP_MS)  # 10


class SensoryPorts(Protocol):
    """World → brain. Must be a pure function of the fly and the arena."""

    @property
    def input_neurons(self) -> torch.Tensor: ...  # engine indices, fixed

    def rates_hz(self, fly: FlyState, arena: Arena) -> torch.Tensor: ...  # one per input


class MotorDecoder(Protocol):
    """Brain → body. Must be a pure function of the readout rates."""

    @property
    def readout_neurons(self) -> torch.Tensor: ...  # engine indices, fixed

    @property
    def window_ms(self) -> int: ...

    def command(self, rates_hz: torch.Tensor, fly: FlyState) -> MotorCommand: ...


@dataclass(frozen=True)
class Pose:
    time_ms: int
    x_mm: float
    y_mm: float
    heading_rad: float
    feeding: bool


class Timeline:
    def __init__(
        self,
        connectome: Connectome,
        arena: Arena,
        senses: SensoryPorts,
        decoder: MotorDecoder,
        seed: int,
        start: FlyState | None = None,
    ) -> None:
        self.arena, self.senses, self.decoder = arena, senses, decoder
        self.brain = Brain(connectome, senses.input_neurons, seed=seed)
        self.fly = start.clone() if start else FlyState()
        readouts = decoder.readout_neurons.to(torch.int64)
        # slot_of[n] = position of neuron n among the readouts, or -1.
        self._slot_of = torch.full((connectome.n_neurons,), -1, dtype=torch.int64)
        self._slot_of[readouts] = torch.arange(len(readouts))
        # Spike counts per readout for each of the last `window_ms` milliseconds (state).
        self.window = torch.zeros((decoder.window_ms, len(readouts)), dtype=torch.int64)

    def step(self) -> Pose:
        """Advance one millisecond of the closed loop."""
        self.brain.set_input_rates(self.senses.rates_hz(self.fly, self.arena))
        counts = torch.zeros(self.window.shape[1], dtype=torch.int64)
        for _ in range(BRAIN_STEPS_PER_WORLD_STEP):
            slots = self._slot_of[self.brain.step()]
            counts.index_add_(0, slots[slots >= 0], torch.ones_like(slots[slots >= 0]))
        self.window[self.fly.time_ms % self.decoder.window_ms] = counts
        rates_hz = self.window.sum(0).to(torch.float64) * (1000.0 / self.decoder.window_ms)
        step_fly(self.fly, self.decoder.command(rates_hz, self.fly), self.arena)
        return Pose(*astuple(self.fly))

    def run(self, duration_ms: int) -> list[Pose]:
        return [self.step() for _ in range(duration_ms)]

    def fork(self) -> Timeline:
        """Brain, body and decoder memory copied; wiring, arena, senses and decoder shared."""
        twin = object.__new__(Timeline)
        twin.__dict__.update(self.__dict__)
        twin.brain = self.brain.fork()
        twin.fly = self.fly.clone()
        twin.window = self.window.clone()
        return twin

    def fingerprint(self) -> str:
        digest = hashlib.sha256(self.brain.state.fingerprint().encode())
        digest.update(self.fly.fingerprint().encode())
        digest.update(self.window.numpy().tobytes())
        return digest.hexdigest()

    def save(self, path: Path) -> None:
        torch.save(
            {
                "brain": self.brain.state.to_dict(),
                "context": self.brain.context(),
                "fly": list(astuple(self.fly)),
                "window": self.window,
            },
            path,
        )

    @classmethod
    def load(
        cls,
        path: Path,
        connectome: Connectome,
        arena: Arena,
        senses: SensoryPorts,
        decoder: MotorDecoder,
    ) -> Timeline:
        saved = torch.load(path, weights_only=True)
        timeline = cls(connectome, arena, senses, decoder, seed=0)
        timeline.brain.check_context(saved["context"], source=str(path))
        timeline.brain.state = BrainState.from_dict(saved["brain"])
        timeline.fly = FlyState(*saved["fly"])
        timeline.window = saved["window"]
        return timeline
