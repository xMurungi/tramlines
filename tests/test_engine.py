"""Unit tests of the engine on tiny hand-built networks."""

import math

import numpy as np
import torch

from tramlines.brain.connectome import from_arrays
from tramlines.brain.engine import Brain, enable_determinism
from tramlines.brain.params import PARAMS


def chain(n: int = 3, synapses: int = 200) -> Brain:
    """Neuron 0 → 1 → ... → n-1, strong enough that each spike makes the next fire."""
    pre = np.arange(n - 1)
    connectome = from_arrays(n, pre, pre + 1, np.full(n - 1, synapses))
    return Brain(connectome, torch.tensor([0]), seed=0)


def test_exact_step_matches_closed_form() -> None:
    # One step from v = rest, g = 1 mV: v should rise by exactly g_to_v.
    tau_m, tau_s, dt = PARAMS.tau_membrane_ms, PARAMS.tau_synapse_ms, PARAMS.dt_ms
    expected = tau_s / (tau_m - tau_s) * (math.exp(-dt / tau_m) - math.exp(-dt / tau_s))
    assert math.isclose(PARAMS.g_to_v, expected)
    brain = chain()
    brain.state.g_mV[1] = 1.0
    brain.step()
    assert math.isclose(brain.state.v_mV[1].item() - PARAMS.v_rest_mV, expected)
    assert math.isclose(brain.state.g_mV[1].item(), math.exp(-dt / tau_s))


def test_spike_travels_with_delay() -> None:
    brain = chain()
    brain.state.v_mV[0] = -40.0  # above threshold: fires at step 0
    record = brain.run(200)
    first = {n: int(record.steps[record.neurons == n].min()) for n in (0, 1, 2)}
    assert first[0] == 0
    # The input lands at step 18; v then takes a few milliseconds to climb past threshold.
    assert first[1] > PARAMS.delay_steps
    assert first[2] - first[1] == first[1] - first[0]  # every hop takes the same time


def test_refractory_neuron_ignores_input() -> None:
    brain = chain()
    brain.state.v_mV[0] = -40.0
    brain.state.v_mV[1] = -40.0  # neuron 1 fires at step 0 too, so is refractory at arrival
    record = brain.run(60)
    assert record.count(1) == 1  # the arrival at step 18 (< 22) is lost


def test_poisson_rate() -> None:
    enable_determinism()
    connectome = from_arrays(50, np.array([0]), np.array([1]), np.array([1]))
    brain = Brain(connectome, torch.arange(50), seed=3)
    brain.set_input_rates(100.0)
    record = brain.run(10_000)
    rate = record.neurons.numel() / 50  # spikes per neuron per second
    assert 90 < rate < 110  # expected ≈ 99.5 Hz (a hit on a firing step is lost)


def test_same_seed_same_spikes() -> None:
    connectome = from_arrays(20, np.arange(19), np.arange(1, 20), np.full(19, 30))
    runs = []
    for _ in range(2):
        brain = Brain(connectome, torch.tensor([0, 5]), seed=42)
        brain.set_input_rates(80.0)
        record = brain.run(3000)
        runs.append((record.steps.tolist(), record.neurons.tolist()))
    assert runs[0] == runs[1]
