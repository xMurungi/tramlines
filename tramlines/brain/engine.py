"""The brain: 138,639 leaky integrate-and-fire neurons stepping through time.

One call to `Brain.step()` advances 0.1 ms in exactly the order Brian2 uses for
the reference model (verified in ADR-0016):

1. integrate v and g exactly over one step, except for refractory neurons;
2. threshold: neurons with v > v_th that are not refractory fire;
3. deliver spikes that left their sender `delay` steps ago (g += w), and
   Poisson input events (v += w_syn * f_poi);
4. reset the neurons that fired (v = v_reset, g = 0).

A refractory neuron ignores input entirely: arrivals in step 3 are lost, not
stored. Brian2 does this for variables marked `(unless refractory)`; we measured
it directly rather than assume it (ADR-0016).
"""

from __future__ import annotations

import copy
import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

import torch

from tramlines.brain.connectome import Connectome
from tramlines.brain.params import PARAMS, LIFParams
from tramlines.brain.state import BrainState, initial_state

DETERMINISM_THREADS = 1


def enable_determinism(threads: int = DETERMINISM_THREADS) -> None:
    """CPU, fixed thread count, deterministic kernels (ADR-0007)."""
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(threads)


def _require_determinism() -> None:
    """A brain refuses to exist outside determinism mode (ADR-0021)."""
    if not torch.are_deterministic_algorithms_enabled():
        raise RuntimeError("call tramlines.brain.engine.enable_determinism() first (ADR-0007)")


@dataclass(frozen=True)
class SpikeRecord:
    """Every spike of a run: spike i is neuron `neurons[i]` at step `steps[i]`."""

    steps: torch.Tensor  # int64
    neurons: torch.Tensor  # int64

    def count(self, neuron: int) -> int:
        return int((self.neurons == neuron).sum())

    def fingerprint(self) -> str:
        """SHA-256 of the whole spike raster: equal fingerprints, identical spikes."""
        digest = hashlib.sha256(self.steps.numpy().tobytes())
        digest.update(self.neurons.numpy().tobytes())
        return digest.hexdigest()


class Brain:
    def __init__(
        self,
        connectome: Connectome,
        input_neurons: torch.Tensor,
        seed: int,
        params: LIFParams = PARAMS,
    ) -> None:
        """`input_neurons` are the indices that can receive Poisson input.

        As in the reference, they have no refractory period (ADR-0014, detail 2).
        Everything set here is fixed for the brain's life and shared by its forks;
        everything that changes lives in `self.state` (ADR-0008, ADR-0021).
        """
        _require_determinism()
        self.connectome = connectome
        self.params = params
        self.input_neurons = input_neurons.to(torch.int64)
        if len(set(self.input_neurons.tolist())) != self.input_neurons.numel():
            raise ValueError("input_neurons must not repeat")
        self.refractory_steps = torch.full(
            (connectome.n_neurons,), params.refractory_steps, dtype=torch.int64
        )
        self.refractory_steps[self.input_neurons] = 0
        self.state = initial_state(
            connectome.n_neurons, len(self.input_neurons), seed=seed, params=params
        )

    def set_input_rates(self, rates_hz: float | torch.Tensor) -> None:
        self.state.input_rates_hz[:] = rates_hz

    def fork(self) -> Brain:
        """A second brain that shares this one's wiring and copies its state (ADR-0008).

        From this instant the two run independently; given the same inputs they
        produce the same future, bit for bit.
        """
        twin = copy.copy(self)  # shares connectome, params, input_neurons, refractory_steps
        twin.state = self.state.clone()
        return twin

    def save(self, path: Path) -> None:
        self.state.save(path, self.context())

    @classmethod
    def load(cls, path: Path, connectome: Connectome, params: LIFParams = PARAMS) -> Brain:
        """Rebuild a brain from a saved state; refuses a state from different wiring."""
        state, context = BrainState.load(path)
        input_neurons = context["input_neurons"]
        assert isinstance(input_neurons, torch.Tensor)
        brain = cls(connectome, input_neurons, seed=0, params=params)
        brain.check_context(context, source=str(path))
        brain.state = state
        return brain

    def context(self) -> dict[str, torch.Tensor | int | str]:
        """What a saved state must be loaded against: wiring, parameters, inputs."""
        return {
            "connectome": self.connectome.fingerprint,
            "params": repr(asdict(self.params)),
            "input_neurons": self.input_neurons,
        }

    def check_context(self, saved: dict[str, object], source: str) -> None:
        if saved["connectome"] != self.connectome.fingerprint:
            raise ValueError(f"{source} was saved from a different connectome")
        if saved["params"] != repr(asdict(self.params)):
            raise ValueError(f"{source} was saved with different model parameters")
        inputs = saved["input_neurons"]
        if not (isinstance(inputs, torch.Tensor) and torch.equal(inputs, self.input_neurons)):
            raise ValueError(f"{source} was saved with different input neurons")

    def step(self) -> torch.Tensor:
        """Advance 0.1 ms. Returns the indices of the neurons that fired."""
        s, p = self.state, self.params

        # 1. Integrate, except refractory neurons, which stay frozen.
        active = (s.step - s.last_spike_step) >= self.refractory_steps
        v_next = (s.v_mV - p.v_rest_mV) * p.decay_v + s.g_mV * p.g_to_v + p.v_rest_mV
        s.v_mV = torch.where(active, v_next, s.v_mV)
        s.g_mV = torch.where(active, s.g_mV * p.decay_g, s.g_mV)

        # 2. Threshold.
        fired = (s.v_mV > p.v_threshold_mV) & active
        fired_idx = torch.nonzero(fired).squeeze(1)
        s.last_spike_step[fired_idx] = s.step
        receptive = active & ~fired

        # 3a. Spikes that left `delay_steps` ago arrive now. Their slot is reused for today's.
        slot = s.step % p.delay_steps
        arriving = torch.nonzero(s.in_flight[slot]).squeeze(1)
        s.in_flight[slot] = fired
        if arriving.numel():
            post, weight = self.connectome.outgoing(arriving)
            s.g_mV.index_add_(0, post, weight * receptive[post])

        # 3b. Poisson input: one draw per input neuron per step, always, so the random
        # stream stays aligned whatever the rates are.
        draws = torch.rand(len(self.input_neurons), generator=s.generator, dtype=torch.float64)
        hits = draws < s.input_rates_hz * (p.dt_ms / 1000.0)
        hits &= receptive[self.input_neurons]
        s.v_mV.index_add_(0, self.input_neurons, hits.to(torch.float64) * p.poisson_kick_mV)

        # 4. Reset.
        s.v_mV[fired_idx] = p.v_reset_mV
        s.g_mV[fired_idx] = 0.0

        s.step += 1
        return fired_idx

    def run(self, n_steps: int) -> SpikeRecord:
        steps: list[torch.Tensor] = []
        neurons: list[torch.Tensor] = []
        for _ in range(n_steps):
            step = self.state.step
            fired = self.step()
            if fired.numel():
                steps.append(torch.full_like(fired, step))
                neurons.append(fired)
        if not neurons:
            empty = torch.zeros(0, dtype=torch.int64)
            return SpikeRecord(steps=empty, neurons=empty.clone())
        return SpikeRecord(steps=torch.cat(steps), neurons=torch.cat(neurons))
