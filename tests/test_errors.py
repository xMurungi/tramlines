"""Realistic connectome errors (owner decision 22): each instrument on the small network."""

from collections.abc import Callable
from functools import cache

import numpy as np
import pytest
import torch
from _scenarios import small

from tramlines.brain.connectome import Connectome, from_arrays
from tramlines.brain.engine import Brain
from tramlines.brain.errors import (
    add_synapses,
    drop_synapses,
    edges_of,
    flip_signs,
    flipped_neurons,
    merge_neurons,
    merge_partners,
    same_sign_per_neuron,
    scaled,
    split_neurons,
    total_synapses,
    with_signs,
)

Instrument = Callable[[Connectome, float, int], Connectome]

INSTRUMENTS: dict[str, Instrument] = {
    "drop": lambda c, r, s: drop_synapses(c, r, s),
    "add anywhere": lambda c, r, s: add_synapses(c, r, s, onto="anywhere"),
    "add existing": lambda c, r, s: add_synapses(c, r, s, onto="existing"),
    "flip": lambda c, r, s: flip_signs(c, r, s),
    "split": lambda c, r, s: split_neurons(c, r, share=0.5, seed=s),
    "merge": lambda c, r, s: merge_neurons(c, r, share=0.5, seed=s),
}


@cache
def wiring() -> Connectome:
    """The small test network, with each neuron's sign drawn once (70% excitatory).

    `_scenarios.small` draws a sign per connection; real FlyWire neurons are purely
    excitatory or inhibitory, and the instruments rely on that.
    """
    e = edges_of_any(small().connectome)
    excitatory = np.random.default_rng(0).random(400) < 0.7
    signed = np.abs(e[2]) * np.where(excitatory[e[0]], 1, -1)
    return from_arrays(400, e[0], e[1], signed)


def edges_of_any(c: Connectome) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    counts = (c.row_start[1:] - c.row_start[:-1]).numpy()
    pre = np.repeat(np.arange(c.n_neurons), counts)
    synapses = np.rint(c.weight_mV.numpy() / 0.275).astype(np.int64)
    return pre, c.post.numpy().astype(np.int64), synapses


def pairs(c: Connectome) -> dict[tuple[int, int], int]:
    """(pre, post) -> signed synapse count."""
    e = edges_of(c)
    return {(int(a), int(b)): int(w) for a, b, w in zip(e.pre, e.post, e.synapses, strict=True)}


def check_valid(c: Connectome) -> None:
    """What the real v783 data guarantees, and every errored brain must keep."""
    e = edges_of(c)  # also: weights are whole synapse counts x w_syn
    assert not (e.pre == e.post).any()
    assert len(np.unique(e.pre * c.n_neurons + e.post)) == len(e.pre)
    assert same_sign_per_neuron(c)
    assert c.n_neurons == wiring().n_neurons


@pytest.mark.parametrize("name", INSTRUMENTS)
def test_zero_rate_is_the_real_brain_bit_for_bit(name: str) -> None:
    real = wiring()
    assert INSTRUMENTS[name](real, 0.0, 3).fingerprint == real.fingerprint


@pytest.mark.parametrize("name", INSTRUMENTS)
def test_seeded_valid_and_different(name: str) -> None:
    real = wiring()
    a, b, other = (INSTRUMENTS[name](real, 0.2, s) for s in (7, 7, 8))
    assert a.fingerprint == b.fingerprint
    assert a.fingerprint != other.fingerprint
    assert a.fingerprint != real.fingerprint
    check_valid(a)


@pytest.mark.parametrize("name", INSTRUMENTS)
def test_errored_brain_runs_deterministically(name: str) -> None:
    """The engine accepts every errored wiring, and two runs agree spike for spike."""
    s = small()
    errored = INSTRUMENTS[name](wiring(), 0.2, 1)
    runs = []
    for _ in range(2):
        brain = Brain(errored, s.inputs, seed=0)
        brain.set_input_rates(150.0)
        runs.append(brain.run(300))
    assert len(runs[0].steps) > 0
    assert torch.equal(runs[0].steps, runs[1].steps)
    assert torch.equal(runs[0].neurons, runs[1].neurons)


def test_drop_loses_synapses_one_at_a_time() -> None:
    real = wiring()
    before = pairs(real)
    after = pairs(drop_synapses(real, 0.3, seed=0))
    total = sum(abs(w) for w in before.values())
    # Binomial(total, 0.7): mean 0.7 total, s.d. about 0.46 sqrt(total); allow 5 s.d.
    kept = sum(abs(w) for w in after.values())
    assert abs(kept - 0.7 * total) < 5 * 0.46 * total**0.5
    # Never gains, never changes sign, never invents a pair.
    assert set(after) <= set(before)
    assert all(abs(after[p]) <= abs(before[p]) and after[p] * before[p] > 0 for p in after)
    # Per synapse, not per connection: strong connections mostly survive, weakened.
    strong = [p for p, w in before.items() if abs(w) >= 20]
    assert all(p in after for p in strong)
    assert any(abs(after[p]) < abs(before[p]) for p in strong)
    assert drop_synapses(real, 1.0, seed=0).n_connections == 0


def test_add_existing_strengthens_only_existing_connections() -> None:
    real = wiring()
    before = pairs(real)
    after = pairs(add_synapses(real, 0.1, seed=0, onto="existing"))
    total = sum(abs(w) for w in before.values())
    assert set(after) == set(before)
    assert sum(abs(w) for w in after.values()) == total + round(0.1 * total)
    assert all(abs(after[p]) >= abs(before[p]) and after[p] * before[p] > 0 for p in after)


def test_add_anywhere_creates_new_weak_pairs_with_the_senders_sign() -> None:
    real = wiring()
    before = pairs(real)
    errored = add_synapses(real, 0.1, seed=0, onto="anywhere")
    after = pairs(errored)
    total = sum(abs(w) for w in before.values())
    assert total_synapses(errored) == total + round(0.1 * total)
    assert set(before) <= set(after)
    new = set(after) - set(before)
    assert new
    sign = edges_of(real).sign_of_neuron()
    assert all(np.sign(after[p]) == sign[p[0]] for p in after)
    # Mostly single synapses, as false positives should be.
    assert np.mean([abs(after[p]) == 1 for p in new]) > 0.8


def test_add_anywhere_never_gives_outputs_to_a_neuron_without_any() -> None:
    real = wiring()
    e = edges_of(real)
    # Silence one neuron's outputs, then check false synapses never start there.
    silent = int(e.pre[0])
    keep = e.pre != silent
    quiet = from_arrays(real.n_neurons, e.pre[keep], e.post[keep], e.synapses[keep])
    errored = edges_of(add_synapses(quiet, 0.5, seed=2))
    assert silent not in set(errored.pre.tolist())


def test_flip_negates_whole_neurons_and_only_them() -> None:
    real = wiring()
    chosen = flipped_neurons(real, 0.1, seed=4)
    senders = np.unique(edges_of(real).pre)
    assert len(chosen) == round(0.1 * len(senders))
    before, after = pairs(real), pairs(flip_signs(real, 0.1, seed=4))
    assert set(before) == set(after)
    for (pre, post), w in before.items():
        assert after[(pre, post)] == (-w if pre in chosen else w)


def test_flip_among_one_group_only() -> None:
    real = wiring()
    group = np.arange(0, 400, 4)  # stands in for "the GABA neurons"
    chosen = flipped_neurons(real, 0.5, seed=1, among=group)
    assert set(chosen.tolist()) <= set(group.tolist())
    assert len(chosen) == round(0.5 * len(np.intersect1d(group, edges_of(real).pre)))
    everything = flip_signs(real, 1.0, seed=0)
    assert torch.equal(everything.weight_mV, -real.weight_mV)


def test_split_removes_whole_connections_of_chosen_neurons_only() -> None:
    real = wiring()
    before = pairs(real)
    after = pairs(split_neurons(real, 0.1, share=0.5, seed=5))
    assert set(after) < set(before)
    assert all(after[p] == before[p] for p in after)  # survivors are untouched
    # share = 1: the chosen neurons lose every connection and nobody else is isolated.
    n_chosen = round(0.1 * real.n_neurons)
    isolated = edges_of(split_neurons(real, 0.1, share=1.0, seed=5))
    degree = np.bincount(isolated.pre, minlength=400) + np.bincount(isolated.post, minlength=400)
    assert (degree == 0).sum() == n_chosen


def test_merge_moves_donor_connections_to_its_host() -> None:
    real = wiring()
    partners = merge_partners(real, 0.05, seed=6)
    hosts, donors = partners[:, 0], partners[:, 1]
    assert len(hosts) == round(0.05 * real.n_neurons)
    assert not set(hosts.tolist()) & set(donors.tolist())
    assert len(set(donors.tolist())) == len(donors)
    before = pairs(real)
    # Each donor is a partner of its host.
    assert all((h, d) in before or (d, h) in before for h, d in partners)
    merged = merge_neurons(real, 0.05, share=1.0, seed=6)
    check_valid(merged)
    after = edges_of(merged)
    # share = 1: donors keep nothing, hosts take it all (minus new self-connections).
    assert not np.isin(after.pre, donors).any() and not np.isin(after.post, donors).any()
    # Host -> donor and donor -> host become host -> host, and are dropped.
    self_loops = sum(
        abs(before.get((int(h), int(d)), 0)) + abs(before.get((int(d), int(h)), 0))
        for h, d in partners
    )
    assert total_synapses(merged) == total_synapses(real) - self_loops
    # The host's sign wins on every output it now sends.
    sign = edges_of(real).sign_of_neuron()
    for h in hosts:
        if sign[h] != 0:
            assert (np.sign(after.synapses[after.pre == h]) == sign[h]).all()


def test_scaled_is_the_control_and_has_no_synapse_counts() -> None:
    real = wiring()
    half = scaled(real, 0.8)
    assert torch.equal(half.weight_mV, real.weight_mV * 0.8)
    assert torch.equal(half.post, real.post)
    with pytest.raises(ValueError, match="whole synapse counts"):
        drop_synapses(half, 0.1, seed=0)


@pytest.mark.parametrize("bad", [-0.1, 1.1])
def test_rates_outside_zero_to_one_are_refused(bad: float) -> None:
    real = wiring()
    with pytest.raises(ValueError):
        drop_synapses(real, bad, seed=0)
    with pytest.raises(ValueError):
        flip_signs(real, bad, seed=0)
    with pytest.raises(ValueError):
        split_neurons(real, 0.1, share=bad, seed=0)
    with pytest.raises(ValueError):
        add_synapses(real, -1.0, seed=0)
    with pytest.raises(ValueError):
        add_synapses(real, 0.1, seed=0, onto="nowhere")  # type: ignore[arg-type]


def test_mixed_sign_wiring_is_refused_where_a_senders_sign_is_needed() -> None:
    mixed = small().connectome  # signs drawn per connection
    assert not same_sign_per_neuron(mixed)
    assert same_sign_per_neuron(wiring())
    with pytest.raises(ValueError, match="both excitatory and inhibitory"):
        add_synapses(mixed, 0.1, seed=0)
    with pytest.raises(ValueError, match="both excitatory and inhibitory"):
        merge_neurons(mixed, 0.1, share=0.5, seed=0)


def test_with_signs_sets_each_neurons_sign_and_zero_keeps_it() -> None:
    real = wiring()
    e = edges_of(real)
    sign = np.zeros(400, dtype=np.int64)
    sign[:10] = -e.sign_of_neuron()[:10]  # flip the first ten
    sign[10:20] = e.sign_of_neuron()[10:20]  # restate the next ten
    before, after = pairs(real), pairs(with_signs(real, sign))
    for (pre, post), w in before.items():
        assert after[(pre, post)] == (-w if pre < 10 else w)
    assert with_signs(real, np.zeros(400, dtype=np.int64)).fingerprint == real.fingerprint
    with pytest.raises(ValueError):
        with_signs(real, np.full(400, 2))
