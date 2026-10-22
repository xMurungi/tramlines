"""Everything a brain *is* at one instant, apart from its wiring.

A fork copies exactly this and nothing else (ADR-0008, ADR-0021). If any mutable
piece of a running brain lived outside `BrainState`, two forks would secretly share
it and their futures would leak into each other; `tests/test_determinism.py` exists
to prove that never happens.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import torch

from tramlines.brain.params import LIFParams

NEVER_SPIKED = -(10**9)  # a step far enough in the past that no neuron starts refractory
STATE_FORMAT = 1  # bump when the saved layout changes


@dataclass
class BrainState:
    step: int  # how many 0.1 ms steps have run
    v_mV: torch.Tensor  # float64 [n]: membrane voltage
    g_mV: torch.Tensor  # float64 [n]: synaptic input
    last_spike_step: torch.Tensor  # int64 [n]: when each neuron last fired
    in_flight: torch.Tensor  # bool [delay_steps, n]: spikes still travelling, by departure step
    input_rates_hz: torch.Tensor  # float64 [k]: current rate of each Poisson input
    generator: torch.Generator = field(repr=False)  # this timeline's own randomness (ADR-0007)

    def clone(self) -> BrainState:
        """An independent copy: changing one never changes the other."""
        generator = torch.Generator(device="cpu")
        generator.set_state(self.generator.get_state())
        return BrainState(
            step=self.step,
            v_mV=self.v_mV.clone(),
            g_mV=self.g_mV.clone(),
            last_spike_step=self.last_spike_step.clone(),
            in_flight=self.in_flight.clone(),
            input_rates_hz=self.input_rates_hz.clone(),
            generator=generator,
        )

    def fingerprint(self) -> str:
        """SHA-256 of every bit of the state, including the random generator.

        Two states with the same fingerprint will produce the same future, bit for bit.
        Comparing raw bytes (not values) also tells -0.0 from 0.0.
        """
        digest = hashlib.sha256(self.step.to_bytes(8, "little", signed=True))
        for tensor in self._tensors().values():
            digest.update(tensor.contiguous().numpy().tobytes())
        return digest.hexdigest()

    def nbytes(self) -> int:
        return sum(t.numel() * t.element_size() for t in self._tensors().values())

    def _tensors(self) -> dict[str, torch.Tensor]:
        return {
            "v_mV": self.v_mV,
            "g_mV": self.g_mV,
            "last_spike_step": self.last_spike_step,
            "in_flight": self.in_flight,
            "input_rates_hz": self.input_rates_hz,
            "generator_state": self.generator.get_state(),
        }

    def to_dict(self) -> dict[str, torch.Tensor | int]:
        """Plain data (tensors and ints), safe to write with `torch.save`."""
        return {"format": STATE_FORMAT, "step": self.step, **self._tensors()}

    @staticmethod
    def from_dict(saved: dict[str, object]) -> BrainState:
        """Inverse of `to_dict`. Consumes the keys it uses."""
        if saved.pop("format") != STATE_FORMAT:
            raise ValueError("state was saved in a different format")
        tensors = {key: saved.pop(key) for key in (*_TENSOR_FIELDS, "generator_state")}
        for key, value in tensors.items():
            if not isinstance(value, torch.Tensor):
                raise ValueError(f"saved state field {key} is not a tensor")
        generator = torch.Generator(device="cpu")
        generator.set_state(tensors.pop("generator_state"))  # type: ignore[arg-type]
        step = saved.pop("step")
        assert isinstance(step, int)
        return BrainState(step=step, generator=generator, **tensors)  # type: ignore[arg-type]

    def save(self, path: Path, context: dict[str, torch.Tensor | int | str]) -> None:
        """Write the state plus `context` (what it must be loaded against) to disk."""
        torch.save({**self.to_dict(), **context}, path)

    @staticmethod
    def load(path: Path) -> tuple[BrainState, dict[str, object]]:
        """Read a saved state. Uses `weights_only=True`: plain data only, no code."""
        saved = torch.load(path, weights_only=True)
        return BrainState.from_dict(saved), saved


_TENSOR_FIELDS = ("v_mV", "g_mV", "last_spike_step", "in_flight", "input_rates_hz")


def initial_state(n_neurons: int, n_inputs: int, seed: int, params: LIFParams) -> BrainState:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    return BrainState(
        step=0,
        v_mV=torch.full((n_neurons,), params.v_rest_mV, dtype=torch.float64),
        g_mV=torch.zeros(n_neurons, dtype=torch.float64),
        last_spike_step=torch.full((n_neurons,), NEVER_SPIKED, dtype=torch.int64),
        in_flight=torch.zeros((params.delay_steps, n_neurons), dtype=torch.bool),
        input_rates_hz=torch.zeros(n_inputs, dtype=torch.float64),
        generator=generator,
    )
