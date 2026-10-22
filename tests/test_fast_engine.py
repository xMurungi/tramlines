"""The fast engine gives exactly the bits of the straightforward one (ADR-0027).

Skipping sleeping neurons must be invisible: same spikes, same state, every step,
including after something outside the engine edits the state.
"""

import pytest
import torch
from _reference_engine import reference_step
from _scenarios import HAVE_DATA, SCHEDULE_HZ, by_name

from tramlines.brain.engine import Brain

SCENARIOS = [
    "small",
    pytest.param("full", marks=pytest.mark.skipif(not HAVE_DATA, reason="needs data")),
]


def side_by_side(brain: Brain, steps: int, nudge_at: int | None = None) -> None:
    reference = brain.state.clone()
    for step in range(steps):
        if step % 100 == 0:
            rate = SCHEDULE_HZ[(step // 100) % len(SCHEDULE_HZ)]
            brain.set_input_rates(rate)
            reference.input_rates_hz[:] = rate
        if step == nudge_at:  # an outside edit to a sleeping neuron must still take effect
            sleeper = int(torch.nonzero(brain.state.v_mV == brain.params.v_rest_mV)[-1])
            brain.state.v_mV[sleeper] = 0.0
            reference.v_mV[sleeper] = 0.0
        fast = brain.step()
        slow = reference_step(brain, reference)
        assert torch.equal(fast, slow), f"spikes differ at step {step}"
    assert brain.state.fingerprint() == reference.fingerprint()


@pytest.mark.parametrize("seed", range(3))
@pytest.mark.parametrize("name", SCENARIOS)
def test_fast_equals_reference(name: str, seed: int) -> None:
    scenario = by_name(name)
    side_by_side(scenario.brain(seed), steps=min(scenario.total_steps, 600))


@pytest.mark.parametrize("name", SCENARIOS)
def test_fast_equals_reference_after_outside_edit(name: str) -> None:
    scenario = by_name(name)
    side_by_side(scenario.brain(0), steps=400, nudge_at=150)


def test_fork_mid_run_keeps_caches_correct() -> None:
    scenario = by_name("small")
    brain = scenario.brain(1)
    brain.set_input_rates(150.0)
    brain.run(250)
    side_by_side(brain.fork(), steps=300)
