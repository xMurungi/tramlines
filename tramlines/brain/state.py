"""Everything a brain *is* at one instant, apart from its wiring.

Phase 1 keeps this as a plain container. Phase 2 adds forking and save/load, and
the sacred tests will prove that nothing mutable lives anywhere else (ADR-0008).
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from tramlines.brain.params import LIFParams

NEVER_SPIKED = -(10**9)  # a step far enough in the past that no neuron starts refractory


@dataclass
class BrainState:
    step: int  # how many 0.1 ms steps have run
    v_mV: torch.Tensor  # float64 [n]: membrane voltage
    g_mV: torch.Tensor  # float64 [n]: synaptic input
    last_spike_step: torch.Tensor  # int64 [n]: when each neuron last fired
    in_flight: torch.Tensor  # bool [delay_steps, n]: spikes still travelling, by departure step
    input_rates_hz: torch.Tensor  # float64 [k]: current rate of each Poisson input
    generator: torch.Generator  # this timeline's own random numbers (ADR-0007)


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
