"""Realistic connectome errors: the kinds of mistakes a reconstruction actually makes.

Owner decision 22, proposal ADR (number assigned by the main session). Result 2
(ADR-0039) scrambled the wiring at random. A real connectome is wrong in specific
ways, each with a published (or unpublished) rate, collected in
`docs/science/connectome-error-rates.md`:

- **missed synapses**: the detector did not see a synapse, or it sits on a twig never
  attached to its neuron (FlyWire attaches 44.7% of postsynapses). Each synapse is
  lost on its own, so a connection weakens by synapse count: `drop_synapses`;
- **false synapses**: the detector saw one that is not there: `add_synapses`;
- **wrong transmitter**: transmitters are predicted per neuron, and the model takes the
  sign from the transmitter, so a wrong prediction can flip all of a neuron's outputs:
  `flip_signs`;
- **split and merge errors**: part of a neuron's arbor missing, or part of another
  neuron's arbor attached to it: `split_neurons`, `merge_neurons`;
- **another published sign**: `with_signs`, for a second transmitter assignment;
- and a control, `scaled`: the same average change in drive with no error pattern.

Every instrument is seeded and deterministic, returns a new `Connectome` with the same
neurons, and keeps what the real data guarantees: no neuron connected to itself, no
pair connected twice, and every neuron purely excitatory or inhibitory. Untouched
connections keep their storage order, so the result is bit-identical to the input
when the error rate is zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from tramlines.brain.connectome import Connectome, from_arrays
from tramlines.brain.params import PARAMS, LIFParams


@dataclass(frozen=True)
class Edges:
    """The wiring as flat arrays: connection k goes from pre[k] to post[k]."""

    n_neurons: int
    pre: np.ndarray  # int64
    post: np.ndarray  # int64
    synapses: np.ndarray  # int64, signed synapse count (W_ij in CLAUDE.md 7.2)

    @property
    def counts(self) -> np.ndarray:
        return np.abs(self.synapses)

    def sign_of_neuron(self) -> np.ndarray:
        """+1 or -1 per neuron from its outgoing connections; 0 if it sends none.

        Refuses wiring in which a neuron sends both signs: v783 has none, and an error
        that copies "the sender's sign" would otherwise pick one at random.
        """
        positive = np.bincount(self.pre, weights=self.synapses > 0, minlength=self.n_neurons)
        negative = np.bincount(self.pre, weights=self.synapses < 0, minlength=self.n_neurons)
        if ((positive > 0) & (negative > 0)).any():
            raise ValueError("a neuron sends both excitatory and inhibitory connections")
        return (positive > 0).astype(np.int64) - (negative > 0).astype(np.int64)


def edges_of(connectome: Connectome, params: LIFParams = PARAMS) -> Edges:
    """Recover signed synapse counts from the weights, refusing anything not a count.

    Weights are stored as signed count x w_syn (`from_arrays`). A connectome whose
    weights are not whole multiples of w_syn (for example one made by `scaled`) has no
    synapse counts, so per-synapse errors on it would mean nothing.
    """
    n = connectome.n_neurons
    counts = (connectome.row_start[1:] - connectome.row_start[:-1]).numpy()
    pre = np.repeat(np.arange(n, dtype=np.int64), counts)
    weight = connectome.weight_mV.numpy()
    synapses = np.rint(weight / params.w_syn_mV).astype(np.int64)
    if not np.array_equal(synapses.astype(np.float64) * params.w_syn_mV, weight):
        raise ValueError("weights are not whole synapse counts x w_syn; cannot add errors")
    if (synapses == 0).any():
        raise ValueError("a stored connection has zero synapses")
    return Edges(n, pre, connectome.post.numpy().astype(np.int64), synapses)


def build(edges: Edges, params: LIFParams = PARAMS) -> Connectome:
    """Back to the engine's layout, dropping connections left with no synapses."""
    keep = edges.synapses != 0
    return from_arrays(
        edges.n_neurons, edges.pre[keep], edges.post[keep], edges.synapses[keep], params
    )


def _check_fraction(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")


def drop_synapses(
    connectome: Connectome, fraction: float, seed: int, params: LIFParams = PARAMS
) -> Connectome:
    """Lose each synapse independently with probability `fraction`.

    A connection of k synapses keeps Binomial(k, 1 - fraction) of them, so strong
    connections weaken and weak ones vanish: a one-synapse connection survives with
    probability 1 - fraction, a twenty-synapse one almost always. This is how missed
    detections act if they are independent, the assumption FlyWire states for its
    5-synapse threshold (Dorkenwald et al. 2024).
    """
    _check_fraction("fraction", fraction)
    e = edges_of(connectome, params)
    kept = np.random.default_rng(seed).binomial(e.counts, 1.0 - fraction)
    return build(Edges(e.n_neurons, e.pre, e.post, np.sign(e.synapses) * kept), params)


def add_synapses(
    connectome: Connectome,
    rate: float,
    seed: int,
    onto: Literal["anywhere", "existing"] = "anywhere",
    params: LIFParams = PARAMS,
) -> Connectome:
    """Add round(rate x total synapses) false synapses.

    Where a false detection lands is not random: it needs two neurites side by side,
    and there are more of those where a neuron already makes and receives many
    synapses. With no geometry in the data, synapse counts are the proxy:

    - ``"anywhere"`` (default): each false synapse's sender is drawn in proportion to
      the neuron's output synapses, its receiver in proportion to the neuron's input
      synapses (never itself). It strengthens an existing connection if the pair is
      already connected, and otherwise creates a new one-synapse connection: new,
      weak paths, the kind a 5-synapse threshold is meant to remove;
    - ``"existing"``: each lands on an existing connection, in proportion to its
      synapse count. No new paths; close to scaling all weights up by (1 + rate),
      with noise. Brackets the effect from the other side.

    Either way a false synapse takes its sender's sign, because the model's sign is a
    property of the sending neuron's transmitter.
    """
    if rate < 0:
        raise ValueError(f"rate must be >= 0, got {rate}")
    e = edges_of(connectome, params)
    rng = np.random.default_rng(seed)
    n_false = round(rate * int(e.counts.sum()))
    if onto == "existing":
        extra = rng.multinomial(n_false, e.counts / e.counts.sum())
        synapses = e.synapses + np.sign(e.synapses) * extra
        return build(Edges(e.n_neurons, e.pre, e.post, synapses), params)
    if onto != "anywhere":
        raise ValueError(f"onto must be 'anywhere' or 'existing', got {onto!r}")
    n = e.n_neurons
    out_synapses = np.bincount(e.pre, weights=e.counts, minlength=n)
    in_synapses = np.bincount(e.post, weights=e.counts, minlength=n)
    pre = rng.choice(n, n_false, p=out_synapses / out_synapses.sum())
    post = rng.choice(n, n_false, p=in_synapses / in_synapses.sum())
    while (self_pair := pre == post).any():
        post[self_pair] = rng.choice(n, int(self_pair.sum()), p=in_synapses / in_synapses.sum())
    key, added = np.unique(pre * n + post, return_counts=True)
    existing_key = e.pre * n + e.post
    order = np.argsort(existing_key)
    # Position of each added pair among the existing ones (clipped: past the end = absent).
    slot = np.minimum(np.searchsorted(existing_key[order], key), len(order) - 1)
    found = np.asarray(existing_key[order[slot]] == key)
    synapses = e.synapses.copy()
    sign = e.sign_of_neuron()
    hit = order[slot[found]]
    synapses[hit] += np.sign(synapses[hit]) * added[found]
    new_pre, new_post = key[~found] // n, key[~found] % n
    return build(
        Edges(
            n,
            np.concatenate([e.pre, new_pre]),
            np.concatenate([e.post, new_post]),
            np.concatenate([synapses, sign[new_pre] * added[~found]]),
        ),
        params,
    )


def neurons_with_outputs(connectome: Connectome) -> np.ndarray:
    return np.flatnonzero((connectome.row_start[1:] > connectome.row_start[:-1]).numpy())


def flipped_neurons(
    connectome: Connectome, fraction: float, seed: int, among: np.ndarray | None = None
) -> np.ndarray:
    """Which neurons `flip_signs` flips (sorted), so a study can log them.

    Exactly round(fraction x candidates) neurons, drawn without replacement, so every
    draw has the stated error rate and draws differ only in *which* neurons. Candidates
    are `among` (default: every neuron), restricted to neurons that send connections:
    a neuron with no outputs has no sign to get wrong.
    """
    _check_fraction("fraction", fraction)
    senders = neurons_with_outputs(connectome)
    candidates = senders if among is None else np.intersect1d(np.asarray(among), senders)
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(candidates, round(fraction * len(candidates)), replace=False))


def flip_signs(
    connectome: Connectome,
    fraction: float,
    seed: int,
    among: np.ndarray | None = None,
    params: LIFParams = PARAMS,
) -> Connectome:
    """Flip excitatory to inhibitory (and back) for a fraction of whole neurons.

    Transmitters are predicted per neuron (Eckstein et al. 2024), so an error makes
    *all* of a neuron's outputs wrong together. Only some mistakes change the model's
    sign: acetylcholine <-> GABA or glutamate does; GABA <-> glutamate does not (both
    inhibitory here); dopamine, serotonin and octopamine count as excitatory. To flip
    one transmitter's neurons, pass their indices as `among`, e.g.
    ``catalog.index_of(catalog.find(top_nt="gaba")).numpy()``. The magnitudes (synapse
    counts) are untouched.
    """
    chosen = flipped_neurons(connectome, fraction, seed, among)
    e = edges_of(connectome, params)
    synapses = np.where(np.isin(e.pre, chosen), -e.synapses, e.synapses)
    return build(Edges(e.n_neurons, e.pre, e.post, synapses), params)


def with_signs(connectome: Connectome, sign: np.ndarray, params: LIFParams = PARAMS) -> Connectome:
    """Give each neuron the sign in `sign` (+1 or -1; 0 keeps the current one).

    Not random: for a second, published assignment of transmitters. The connectivity
    file's signs and the v2.1.0 annotations' `top_nt` (acetylcholine, dopamine,
    serotonin, octopamine excitatory; GABA, glutamate inhibitory) disagree for about
    4.4% of neurons, which is an error of exactly the kind this module asks about.
    """
    sign = np.asarray(sign, dtype=np.int64)
    if sign.shape != (connectome.n_neurons,) or not np.isin(sign, (-1, 0, 1)).all():
        raise ValueError("sign must hold -1, 0 or +1 for every neuron")
    e = edges_of(connectome, params)
    synapses = np.where(sign[e.pre] == 0, e.synapses, sign[e.pre] * e.counts)
    return build(Edges(e.n_neurons, e.pre, e.post, synapses), params)


def _chosen_neurons(
    connectome: Connectome, fraction: float, rng: np.random.Generator
) -> np.ndarray:
    """round(fraction x connected neurons), without replacement; never isolated neurons."""
    _check_fraction("fraction", fraction)
    out_degree = (connectome.row_start[1:] - connectome.row_start[:-1]).numpy()
    degree = out_degree + np.bincount(connectome.post.numpy(), minlength=connectome.n_neurons)
    connected = np.flatnonzero(degree > 0)
    return np.sort(rng.choice(connected, round(fraction * len(connected)), replace=False))


def split_neurons(
    connectome: Connectome,
    fraction: float,
    share: float,
    seed: int,
    params: LIFParams = PARAMS,
) -> Connectome:
    """A split error: for a fraction of neurons, part of the arbor is missing.

    A piece of arbor cut off from its neuron takes its synapses with it, and synapses
    between two neurons tend to sit close together, so the loss is correlated: here a
    chosen neuron loses each of its connections (incoming and outgoing) *whole*, with
    probability `share`. `drop_synapses` is the opposite, independent extreme; between
    them they bracket how incompleteness acts. A connection between two chosen neurons
    can be lost from either end. With no synapse positions in the data, which
    connections share a twig cannot be known, so the choice is random.
    """
    _check_fraction("share", share)
    rng = np.random.default_rng(seed)
    chosen = np.zeros(connectome.n_neurons, dtype=bool)
    chosen[_chosen_neurons(connectome, fraction, rng)] = True
    e = edges_of(connectome, params)
    # Two draws per connection, one for each end, always made: the same connection gets
    # the same fate for the same seed whatever else is chosen.
    lost_at_sender = chosen[e.pre] & (rng.random(len(e.pre)) < share)
    lost_at_receiver = chosen[e.post] & (rng.random(len(e.pre)) < share)
    synapses = np.where(lost_at_sender | lost_at_receiver, 0, e.synapses)
    return build(Edges(e.n_neurons, e.pre, e.post, synapses), params)


def merge_partners(connectome: Connectome, fraction: float, seed: int) -> np.ndarray:
    """The (host, donor) pairs `merge_neurons` uses, shape [k, 2], so a study can log them.

    Hosts are round(fraction x connected neurons). A merge joins neurites that touch,
    and connected neurons touch by definition, so each host's donor is drawn from its
    own partners (inputs or outputs). No neuron is both host and donor, and each donor
    gives to one host; a host whose partners are all taken gets none (rare at small
    fractions).
    """
    rng = np.random.default_rng(seed)
    hosts = _chosen_neurons(connectome, fraction, rng)
    rng.shuffle(hosts)
    post = connectome.post.numpy().astype(np.int64)
    row_start = connectome.row_start.numpy()
    by_receiver = np.argsort(post, kind="stable")
    receiver_start = np.searchsorted(post[by_receiver], np.arange(connectome.n_neurons + 1))
    counts = row_start[1:] - row_start[:-1]
    pre = np.repeat(np.arange(connectome.n_neurons, dtype=np.int64), counts)
    taken = np.zeros(connectome.n_neurons, dtype=bool)
    taken[hosts] = True
    pairs: list[tuple[int, int]] = []
    for host in hosts:
        outputs = post[row_start[host] : row_start[host + 1]]
        inputs = pre[by_receiver[receiver_start[host] : receiver_start[host + 1]]]
        partners = np.unique(np.concatenate([outputs, inputs]))
        partners = partners[~taken[partners]]
        if len(partners) == 0:
            continue
        donor = int(rng.choice(partners))
        taken[donor] = True
        pairs.append((int(host), donor))
    return np.array(pairs, dtype=np.int64).reshape(-1, 2)


def merge_neurons(
    connectome: Connectome,
    fraction: float,
    share: float,
    seed: int,
    params: LIFParams = PARAMS,
) -> Connectome:
    """A merge error: part of a neighbour's arbor wrongly attached to a neuron.

    For each (host, donor) pair from `merge_partners`, each of the donor's connections
    moves to the host with probability `share`: the donor's inputs become the host's
    inputs, and its outputs become the host's outputs, with the host's sign (a neuron's
    transmitter is called by majority over its synapses, which stay mostly the host's).
    The neuron count is unchanged: the donor keeps the rest of its arbor. Connections
    that become self-connections are dropped (the data has none); repeated pairs are
    summed into one connection.
    """
    _check_fraction("share", share)
    pairs = merge_partners(connectome, fraction, seed)
    e = edges_of(connectome, params)
    host_of = np.arange(e.n_neurons, dtype=np.int64)
    host_of[pairs[:, 1]] = pairs[:, 0]
    is_donor = np.zeros(e.n_neurons, dtype=bool)
    is_donor[pairs[:, 1]] = True
    rng = np.random.default_rng([seed, 1])  # a stream separate from the pair choice
    move_out = is_donor[e.pre] & (rng.random(len(e.pre)) < share)
    move_in = is_donor[e.post] & (rng.random(len(e.pre)) < share)
    sign = e.sign_of_neuron()
    pre = np.where(move_out, host_of[e.pre], e.pre)
    post = np.where(move_in, host_of[e.post], e.post)
    # A moved output takes the host's sign; a host that sends nothing keeps the donor's.
    new_sign = np.where(move_out & (sign[pre] != 0), sign[pre], np.sign(e.synapses))
    synapses = new_sign * e.counts
    synapses[pre == post] = 0
    # Sum repeated pairs into the first of them, keeping storage order otherwise.
    key = pre * e.n_neurons + post
    _, first, inverse = np.unique(key, return_index=True, return_inverse=True)
    summed = np.zeros(len(first), dtype=np.int64)
    np.add.at(summed, inverse, synapses)
    merged = np.zeros_like(synapses)
    merged[first] = summed
    return build(Edges(e.n_neurons, pre, post, merged), params)


def scaled(connectome: Connectome, factor: float) -> Connectome:
    """The control: every weight times `factor`, no pattern of errors.

    Dropping 20% of synapses also lowers the average drive by 20%. Comparing with
    `scaled(c, 0.8)` separates what the *pattern* of loss does from what the lower
    average does. The result has no whole synapse counts, so the other instruments
    refuse it.
    """
    if factor < 0:
        raise ValueError(f"factor must be >= 0, got {factor}")
    return Connectome(
        n_neurons=connectome.n_neurons,
        row_start=connectome.row_start.clone(),
        post=connectome.post.clone(),
        weight_mV=connectome.weight_mV * factor,
    )


def total_synapses(connectome: Connectome, params: LIFParams = PARAMS) -> int:
    return int(edges_of(connectome, params).counts.sum())


def same_sign_per_neuron(connectome: Connectome, params: LIFParams = PARAMS) -> bool:
    """True if every neuron's outgoing weights are all positive or all negative."""
    try:
        edges_of(connectome, params).sign_of_neuron()
    except ValueError:
        return False
    return True
