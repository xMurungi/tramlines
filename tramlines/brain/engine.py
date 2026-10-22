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
SLEEP_EVERY_STEPS = 10  # how often settled neurons leave the awake set; speed only


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
        self._is_input = torch.zeros(connectome.n_neurons, dtype=torch.bool)
        self._is_input[self.input_neurons] = True
        self.state = initial_state(
            connectome.n_neurons, len(self.input_neurons), seed=seed, params=params
        )
        # Speed caches (ADR-0027), built from the state on the first step.
        self._awake = torch.zeros(0, dtype=torch.int64)
        self._is_awake = torch.zeros(0, dtype=torch.bool)
        self._awake_refractory = torch.zeros(0, dtype=torch.int64)
        self._in_flight: list[torch.Tensor] = []
        self._cache_key: tuple[int, ...] = ()

    def set_input_rates(self, rates_hz: float | torch.Tensor) -> None:
        self.state.input_rates_hz[:] = rates_hz

    def fork(self) -> Brain:
        """A second brain that shares this one's wiring and copies its state (ADR-0008).

        From this instant the two run independently; given the same inputs they
        produce the same future, bit for bit.
        """
        self._ensure_caches()
        twin = copy.copy(self)  # shares connectome, params, input_neurons, refractory_steps
        twin.state = self.state.clone()
        twin._is_awake = self._is_awake.clone()  # speed caches: copied, not rebuilt
        twin._in_flight = list(self._in_flight)  # (entries are replaced, never edited)
        twin._cache_key = twin._key()
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
        """Advance 0.1 ms. Returns the indices of the neurons that fired, ascending.

        Only *awake* neurons are computed (ADR-0027). A neuron exactly at rest with
        zero synaptic input is left exactly unchanged by the update below, so
        skipping it gives the same bits as computing it. Most of the brain is asleep.
        """
        self._ensure_caches()
        s, p = self.state, self.params
        awake = self._awake

        # 1. Integrate, except refractory neurons, which stay frozen.
        # (index_select / index_copy_ only move data: same bits as plain indexing, faster.)
        active = (s.step - s.last_spike_step.index_select(0, awake)) >= self._awake_refractory
        v, g = s.v_mV.index_select(0, awake), s.g_mV.index_select(0, awake)
        v_next = (v - p.v_rest_mV) * p.decay_v + g * p.g_to_v + p.v_rest_mV
        v = torch.where(active, v_next, v)
        g = torch.where(active, g * p.decay_g, g)
        s.v_mV.index_copy_(0, awake, v)
        s.g_mV.index_copy_(0, awake, g)

        # 2. Threshold.
        fired_idx = torch.sort(awake[(v > p.v_threshold_mV) & active]).values
        s.last_spike_step.index_fill_(0, fired_idx, s.step)

        # 3a. Spikes that left `delay_steps` ago arrive now. Their slot is reused for today's.
        slot = s.step % p.delay_steps
        arriving = self._in_flight[slot]
        self._in_flight[slot] = fired_idx
        s.in_flight[slot].index_fill_(0, arriving, False)
        s.in_flight[slot].index_fill_(0, fired_idx, True)
        if arriving.numel():
            post, weight = self.connectome.outgoing(arriving)
            s.g_mV.index_add_(0, post, weight * self._receptive(post))
            self._wake(post)

        # 3b. Poisson input: one draw per input neuron per step, always, so the random
        # stream stays aligned whatever the rates are.
        draws = torch.rand(len(self.input_neurons), generator=s.generator, dtype=torch.float64)
        hits = draws < s.input_rates_hz * (p.dt_ms / 1000.0)
        hits &= self._receptive(self.input_neurons)
        s.v_mV.index_add_(0, self.input_neurons, hits.to(torch.float64) * p.poisson_kick_mV)

        # 4. Reset.
        s.v_mV.index_fill_(0, fired_idx, p.v_reset_mV)
        s.g_mV.index_fill_(0, fired_idx, 0.0)

        s.step += 1
        if s.step % SLEEP_EVERY_STEPS == 0:
            self._sleep()
        self._cache_key = self._key()
        return fired_idx

    # --- Speed caches (ADR-0027). Derived from the state, never part of it. ---

    def _receptive(self, neurons: torch.Tensor) -> torch.Tensor:
        """Not refractory, and did not fire this step (a refractory neuron ignores input)."""
        neurons = neurons.to(torch.int64)
        last = self.state.last_spike_step.index_select(0, neurons)
        step = self.state.step
        return ((step - last) >= self.refractory_steps.index_select(0, neurons)) & (last != step)

    def _wake(self, neurons: torch.Tensor) -> None:
        new = neurons[~self._is_awake[neurons]]
        if new.numel():
            new = torch.unique(new.to(torch.int64))
            self._is_awake[new] = True
            self._awake = torch.cat([self._awake, new])
            self._awake_refractory = self.refractory_steps.index_select(0, self._awake)

    def _sleep(self) -> None:
        """Drop neurons that are exactly back at rest; they cannot change until woken."""
        s, awake = self.state, self._awake
        keep = (s.v_mV[awake] != self.params.v_rest_mV) | (s.g_mV[awake] != 0.0)
        keep |= self._is_input[awake]
        self._is_awake[awake[~keep]] = False
        self._awake = awake[keep]
        self._awake_refractory = self.refractory_steps.index_select(0, self._awake)

    def _key(self) -> tuple[int, ...]:
        """Changes whenever anything outside the engine replaces or edits the state."""
        s = self.state
        return (
            id(s),
            s.step,
            id(s.v_mV),
            s.v_mV._version,
            id(s.g_mV),
            s.g_mV._version,
            id(s.in_flight),
            s.in_flight._version,
        )

    def _ensure_caches(self) -> None:
        if self._cache_key == self._key():
            return
        s = self.state
        at_rest = (s.v_mV == self.params.v_rest_mV) & (s.g_mV == 0.0)
        self._is_awake = ~at_rest | self._is_input
        self._awake = torch.nonzero(self._is_awake).squeeze(1)
        self._awake_refractory = self.refractory_steps.index_select(0, self._awake)
        self._in_flight = [torch.nonzero(row).squeeze(1) for row in s.in_flight]
        self._cache_key = self._key()

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
