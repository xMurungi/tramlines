"""The straightforward engine: every neuron, every step, nothing skipped.

This is `Brain.step()` as it was before the speed work (ADR-0027), kept as the
yardstick the fast engine must match bit for bit. It works on a cloned
`BrainState`, so it can run alongside a real `Brain` from the same moment.
"""

import torch

from tramlines.brain.engine import Brain
from tramlines.brain.state import BrainState


def reference_step(brain: Brain, s: BrainState) -> torch.Tensor:
    p = brain.params
    active = (s.step - s.last_spike_step) >= brain.refractory_steps
    v_next = (s.v_mV - p.v_rest_mV) * p.decay_v + s.g_mV * p.g_to_v + p.v_rest_mV
    s.v_mV = torch.where(active, v_next, s.v_mV)
    s.g_mV = torch.where(active, s.g_mV * p.decay_g, s.g_mV)

    fired = (s.v_mV > p.v_threshold_mV) & active
    fired_idx = torch.nonzero(fired).squeeze(1)
    s.last_spike_step[fired_idx] = s.step
    receptive = active & ~fired

    slot = s.step % p.delay_steps
    arriving = torch.nonzero(s.in_flight[slot]).squeeze(1)
    s.in_flight[slot] = fired
    if arriving.numel():
        post, weight = brain.connectome.outgoing(arriving)
        s.g_mV.index_add_(0, post, weight * receptive[post])

    draws = torch.rand(len(brain.input_neurons), generator=s.generator, dtype=torch.float64)
    hits = draws < s.input_rates_hz * (p.dt_ms / 1000.0)
    hits &= receptive[brain.input_neurons]
    s.v_mV.index_add_(0, brain.input_neurons, hits.to(torch.float64) * p.poisson_kick_mV)

    s.v_mV[fired_idx] = p.v_reset_mV
    s.g_mV[fired_idx] = 0.0
    s.step += 1
    return fired_idx
