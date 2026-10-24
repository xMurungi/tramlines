"""The null brain: the same neurons and the same amount of wiring, connected at random.

ADR-0035, Result 2; the shuffle is ADR-0039. To ask what the real wiring contributes
to behaviour, compare the fly with one whose brain keeps everything except *who
connects to whom*. Every connection keeps its sender and its signed weight; only its
receiver is drawn again. So each neuron keeps:

- how many connections it sends (out-degree), with the same weights and the same
  sign (each FlyWire neuron is purely excitatory or inhibitory, and stays so);
- how many connections it receives (in-degree);

but not which neurons those are, nor the balance of excitation and inhibition it
receives. Like the real wiring, the null brain has no neuron connected to itself and
no pair connected twice.
"""

from __future__ import annotations

import numpy as np
import torch

from tramlines.brain.connectome import Connectome

MAX_REPAIR_ROUNDS = 200


def shuffled(connectome: Connectome, seed: int, fraction: float = 1.0) -> Connectome:
    """A degree-preserving random rewiring of `connectome`, the same for the same seed.

    Only a random `fraction` of connections is rewired (1.0 = all, the full null brain);
    their receivers are shuffled among themselves, so degrees are kept either way.

    Permuting the receiver column across all connections keeps every out-degree (the
    senders do not move) and every in-degree (each receiver appears as often as
    before). The permutation creates a few self-connections and repeated pairs
    (about 0.4% on v783); each is repaired by swapping its receiver with that of a
    randomly chosen connection, which also keeps every degree.
    """
    rng = np.random.default_rng(seed)
    n = connectome.n_neurons
    counts = (connectome.row_start[1:] - connectome.row_start[:-1]).numpy()
    pre = np.repeat(np.arange(n, dtype=np.int64), counts)
    post = connectome.post.numpy().astype(np.int64).copy()
    if fraction >= 1.0:
        chosen = np.arange(len(post))
    else:
        chosen = np.sort(rng.choice(len(post), round(fraction * len(post)), replace=False))
    post[chosen] = post[chosen][rng.permutation(len(chosen))]
    rewired = None if fraction >= 1.0 else np.isin(np.arange(len(post)), chosen)
    for _ in range(MAX_REPAIR_ROUNDS):
        bad = _invalid(pre, post, n, rewired)
        if len(bad) == 0:
            break
        # Only rewired connections are repaired, and only with each other.
        partner = chosen[rng.integers(0, len(chosen), len(bad))]
        # Each swap must touch two distinct connections, and none twice, so that the
        # receivers are only exchanged, never copied (copying would change in-degrees).
        _, first = np.unique(partner, return_index=True)
        keep = np.zeros(len(bad), dtype=bool)
        keep[first] = True
        keep &= ~np.isin(partner, bad)
        bad, partner = bad[keep], partner[keep]
        post[bad], post[partner] = post[partner], post[bad].copy()
    else:
        raise RuntimeError(f"could not remove repeated pairs in {MAX_REPAIR_ROUNDS} rounds")
    return Connectome(
        n_neurons=n,
        row_start=connectome.row_start.clone(),
        post=torch.from_numpy(post.astype(np.int32)),
        weight_mV=connectome.weight_mV.clone(),
    )


def _invalid(pre: np.ndarray, post: np.ndarray, n: int, movable: np.ndarray | None) -> np.ndarray:
    """Positions to repair: self-connections, and repeated pairs.

    With every connection movable, each repeat of a pair after its first. When only some
    are (`movable`, a partial shuffle), every movable member of a repeated pair, so that
    an untouched connection is never the one moved.
    """
    key = pre * n + post
    _, first, count = np.unique(key, return_index=True, return_counts=True)
    if movable is None:
        repeat = np.ones(len(key), dtype=bool)
        repeat[first] = False
        return np.flatnonzero(repeat | (pre == post))
    _, inverse = np.unique(key, return_inverse=True)
    repeat = count[inverse] > 1
    return np.flatnonzero((repeat | (pre == post)) & movable)
