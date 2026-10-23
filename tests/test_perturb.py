"""Imperfect knowledge for the ghost (ADR-0035, Result 1)."""

import torch
from _scenarios import small

from tramlines.brain.engine import Brain
from tramlines.brain.params import PARAMS
from tramlines.timeline.perturb import Knowledge, blur


def moment() -> Brain:
    """A busy small brain, 40 ms into a run."""
    brain = small().brain(0)
    brain.set_input_rates(150.0)
    brain.run(400)
    return brain


def test_voltage_error_has_the_requested_size_and_spares_the_random_stream() -> None:
    brain = moment()
    before_v = brain.state.v_mV.clone()
    before_rng = brain.state.generator.get_state().clone()
    blur(brain.state, Knowledge("voltage", 1e-6, seed=1))
    error = brain.state.v_mV - before_v
    assert 0.5e-6 < float(error.abs().mean()) < 1.5e-6
    assert torch.equal(brain.state.generator.get_state(), before_rng)  # same future inputs


def test_float32_rounds_the_state() -> None:
    brain = moment()
    blur(brain.state, Knowledge("float32"))
    v = brain.state.v_mV
    assert torch.equal(v, v.to(torch.float32).to(torch.float64))


def test_drop_spike_removes_exactly_one_spike_in_transit() -> None:
    brain = moment()
    before = int(brain.state.in_flight.sum())
    assert before > 0
    blur(brain.state, Knowledge("drop_spike", seed=3))
    assert int(brain.state.in_flight.sum()) == before - 1


def test_partial_observation_assumes_unseen_neurons_at_rest() -> None:
    brain = moment()
    blur(brain.state, Knowledge("partial", 0.5, seed=2))
    at_rest = (brain.state.v_mV == PARAMS.v_rest_mV) & (brain.state.g_mV == 0.0)
    assert float(at_rest.double().mean()) > 0.45  # about half reset (plus any already at rest)


def test_same_seed_same_error() -> None:
    a, b = moment(), moment()
    blur(a.state, Knowledge("voltage", 1e-3, seed=7))
    blur(b.state, Knowledge("voltage", 1e-3, seed=7))
    assert a.state.fingerprint() == b.state.fingerprint()
