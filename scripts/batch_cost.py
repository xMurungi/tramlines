"""What would 8 batched futures cost compared with one? (ADR-0029)

Times the per-step work of the engine (gather the awake neurons, integrate,
threshold, write back, deliver spikes, draw Poisson input) on one timeline and
on a batch of B timelines sharing one awake set, in two memory layouts:
batch-major [B, N] and neuron-major [N, B] (each neuron's B copies side by side).
A prototype of the arithmetic, not the batched engine itself.

    uv run python scripts/batch_cost.py
"""

from __future__ import annotations

import time

import torch

from tramlines.brain.engine import enable_determinism
from tramlines.brain.params import PARAMS as P

N = 138_639
STEPS = 2000


def step_cost_us(
    batch: int, awake_count: int, spikes_per_step: int, fanout: int, neuron_major: bool
) -> float:
    gen = torch.Generator().manual_seed(0)
    shape, dim = ((N, batch), 0) if neuron_major else ((batch, N), 1)
    v = torch.full(shape, P.v_rest_mV, dtype=torch.float64)
    g = torch.zeros(shape, dtype=torch.float64)
    last = torch.full(shape, -(10**9), dtype=torch.int64)
    refractory = torch.full((N,), P.refractory_steps, dtype=torch.int64)
    awake = torch.randperm(N, generator=gen)[:awake_count]
    refractory_awake = refractory.index_select(0, awake)
    refractory_awake = refractory_awake.unsqueeze(1) if neuron_major else refractory_awake
    posts = torch.randint(N, (batch, spikes_per_step * fanout), generator=gen)
    weights = torch.rand((batch, spikes_per_step * fanout), generator=gen, dtype=torch.float64)
    inputs = torch.randperm(N, generator=gen)[:277]
    rates = torch.full((batch, 277), 100.0, dtype=torch.float64)

    start = time.perf_counter()
    for step in range(STEPS):
        active = (step - last.index_select(dim, awake)) >= refractory_awake
        va, ga = v.index_select(dim, awake), g.index_select(dim, awake)
        v_next = (va - P.v_rest_mV) * P.decay_v + ga * P.g_to_v + P.v_rest_mV
        va = torch.where(active, v_next, va)
        ga = torch.where(active, ga * P.decay_g, ga)
        v.index_copy_(dim, awake, va)
        g.index_copy_(dim, awake, ga)
        fired = (va > P.v_threshold_mV) & active
        torch.nonzero(fired)
        if neuron_major:
            flat = (posts * batch + torch.arange(batch).unsqueeze(1)).reshape(-1)
        else:
            flat = (posts + torch.arange(batch).unsqueeze(1) * N).reshape(-1)
        g.view(-1).index_add_(0, flat, weights.reshape(-1))
        hits = torch.rand((batch, 277), generator=gen, dtype=torch.float64) < rates * 1e-4
        kick = hits.to(torch.float64) * P.poisson_kick_mV
        v.index_add_(dim, inputs, kick.T if neuron_major else kick)
    return (time.perf_counter() - start) / STEPS * 1e6


def main() -> None:
    enable_determinism()
    print("layout         awake  batch   us/step   per-timeline   vs one")
    for neuron_major in (False, True):
        layout = "neuron-major" if neuron_major else "batch-major"
        for awake_count, spikes in [(7_300, 2), (43_000, 25)]:
            one = step_cost_us(1, awake_count, spikes, 110, neuron_major)
            for batch in (1, 8):
                cost = (
                    one
                    if batch == 1
                    else step_cost_us(batch, awake_count, spikes, 110, neuron_major)
                )
                print(
                    f"{layout:13} {awake_count:6} {batch:6} {cost:9.1f} {cost / batch:12.1f}"
                    f"   {cost / one:5.2f}x for {batch} futures"
                )


if __name__ == "__main__":
    main()
