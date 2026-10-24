"""How different are two futures? (CLAUDE.md Phase 5: divergence metrics.)

Two timelines that started from the same moment are compared step by step:
how far apart the flies are, how many spikes one brain fired that the other did
not, and (for the backward horizon, ADR-0040) how far apart the brains' states are.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import torch

from tramlines.brain.engine import Brain, SpikeRecord
from tramlines.timeline.timeline import Pose


def path_distance_mm(a: Sequence[Pose], b: Sequence[Pose]) -> list[float]:
    """Distance between the two flies at each millisecond."""
    return [math.hypot(p.x_mm - q.x_mm, p.y_mm - q.y_mm) for p, q in zip(a, b, strict=True)]


def first_divergence_ms(distances: Sequence[float], epsilon_mm: float) -> int | None:
    """The first millisecond at which the flies are more than `epsilon_mm` apart."""
    return next((t for t, d in enumerate(distances) if d > epsilon_mm), None)


def spike_differences(a: SpikeRecord, b: SpikeRecord, n_neurons: int, bin_steps: int) -> list[int]:
    """Spikes in one raster but not the other (Hamming distance), per time bin."""

    def keys(record: SpikeRecord) -> torch.Tensor:
        return record.steps * n_neurons + record.neurons

    ka, kb = keys(a), keys(b)
    only = torch.cat([ka[~torch.isin(ka, kb)], kb[~torch.isin(kb, ka)]])
    if not only.numel():
        return []
    bins = torch.div(only // n_neurons, bin_steps, rounding_mode="floor")
    return torch.bincount(bins).tolist()


@dataclass(frozen=True)
class BrainDifference:
    """How far apart two brains' states are right now (ADR-0040)."""

    max_dv_mV: float  # largest voltage difference over all neurons
    max_dg_mV: float  # largest synaptic-input difference
    discrete_equal: bool  # same spikes in transit, refractory neurons and random stream

    def below(self, epsilon_mV: float) -> bool:
        """Could a demon measuring to `epsilon_mV` tell these brains apart? False if so."""
        return self.discrete_equal and max(self.max_dv_mV, self.max_dg_mV) < epsilon_mV


def brain_difference(a: Brain, b: Brain) -> BrainDifference:
    """Compare everything that shapes the brains' futures.

    The engine also stores each neuron's last spike time; it only matters while the
    neuron is refractory, so the refractory flags (the engine's own test for the
    next step) stand in for it.
    """
    sa, sb = a.state, b.state

    def refractory(brain: Brain) -> torch.Tensor:
        return (brain.state.step - brain.state.last_spike_step) < brain.refractory_steps

    discrete = (
        sa.step == sb.step
        and torch.equal(sa.in_flight, sb.in_flight)
        and torch.equal(refractory(a), refractory(b))
        and torch.equal(sa.generator.get_state(), sb.generator.get_state())
    )
    return BrainDifference(
        max_dv_mV=float((sa.v_mV - sb.v_mV).abs().max()),
        max_dg_mV=float((sa.g_mV - sb.g_mV).abs().max()),
        discrete_equal=discrete,
    )
