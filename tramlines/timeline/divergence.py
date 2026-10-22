"""How different are two futures? (CLAUDE.md Phase 5: divergence metrics.)

Two timelines that started from the same moment are compared step by step:
how far apart the flies are, and how many spikes one brain fired that the
other did not.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import torch

from tramlines.brain.engine import SpikeRecord
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
