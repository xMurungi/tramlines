"""Divergence measures and recording a timeline's spikes (ADR-0029)."""

import torch
from _scenarios import timeline_small

from tramlines.brain.engine import SpikeRecord
from tramlines.timeline.divergence import (
    brain_difference,
    first_divergence_ms,
    path_distance_mm,
    spike_differences,
)
from tramlines.timeline.perturb import Knowledge, blur
from tramlines.timeline.timeline import Pose


def pose(t: int, x: float) -> Pose:
    return Pose(t, x, 0.0, 0.0, False, False)


def test_path_distance_and_first_divergence() -> None:
    a = [pose(t, 0.0) for t in range(4)]
    b = [pose(0, 0.0), pose(1, 0.05), pose(2, 0.3), pose(3, 0.0)]
    distances = path_distance_mm(a, b)
    assert distances == [0.0, 0.05, 0.3, 0.0]
    assert first_divergence_ms(distances, epsilon_mm=0.1) == 2
    assert first_divergence_ms([0.0, 0.0], epsilon_mm=0.1) is None


def test_spike_differences_count_only_mismatches() -> None:
    a = SpikeRecord(steps=torch.tensor([0, 5, 12]), neurons=torch.tensor([1, 2, 3]))
    b = SpikeRecord(steps=torch.tensor([0, 5, 15]), neurons=torch.tensor([1, 4, 3]))
    # Mismatches: (5,2), (12,3) only in a; (5,4), (15,3) only in b. Bins of 10 steps.
    assert spike_differences(a, b, n_neurons=10, bin_steps=10) == [2, 2]
    assert spike_differences(a, a, n_neurons=10, bin_steps=10) == []


def test_run_recording_matches_plain_run() -> None:
    scenario = timeline_small()
    recorded, plain = scenario.timeline(0), scenario.timeline(0)
    poses, spikes = recorded.run_recording(50)
    assert poses == plain.run(50)
    assert recorded.fingerprint() == plain.fingerprint()
    assert spikes.neurons.numel() > 0


def test_brain_difference_sees_voltages_spikes_and_nothing_else() -> None:
    from _scenarios import small

    brain = small().brain(0)
    brain.set_input_rates(150.0)
    brain.run(400)
    twin = brain.fork()
    same = brain_difference(brain, twin)
    assert same.discrete_equal and same.max_dv_mV == 0.0 and same.below(1e-300)

    blur(twin.state, Knowledge("voltage", 1e-6, seed=1))
    blurred = brain_difference(brain, twin)
    assert blurred.discrete_equal and 0 < blurred.max_dv_mV < 1e-4
    assert blurred.below(1e-3) and not blurred.below(1e-9)

    other = brain.fork()
    quiet = next(int(n) for n in range(400) if other.state.last_spike_step[n] < 0)
    other.inject_spike(quiet)
    assert not brain_difference(brain, other).discrete_equal
