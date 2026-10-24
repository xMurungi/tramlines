"""The null brain: a degree-preserving shuffle of the wiring (ADR-0035 Result 2, ADR-0039)."""

import numpy as np
import pytest
import torch
from _scenarios import HAVE_DATA, small

from tramlines.brain.connectome import Connectome
from tramlines.brain.null import shuffled


def edges(c: Connectome) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    counts = (c.row_start[1:] - c.row_start[:-1]).numpy()
    pre = np.repeat(np.arange(c.n_neurons), counts)
    return pre, c.post.numpy().astype(np.int64), c.weight_mV.numpy()


def check_null(real: Connectome, null: Connectome) -> None:
    pre, post, w = edges(real)
    null_pre, null_post, null_w = edges(null)
    n = real.n_neurons
    # Out-degree, and each sender's weights (so its sign), unchanged.
    assert torch.equal(null.row_start, real.row_start)
    assert np.array_equal(null_pre, pre) and np.array_equal(null_w, w)
    # In-degree unchanged.
    assert np.array_equal(np.bincount(null_post, minlength=n), np.bincount(post, minlength=n))
    # Like the real wiring: no self-connections, no repeated pairs.
    assert not (null_pre == null_post).any()
    assert len(np.unique(null_pre * n + null_post)) == len(null_post)
    # Actually rewired: most connections now go somewhere else.
    kept = np.isin(null_pre * n + null_post, pre * n + post).mean()
    assert kept < 0.2


def test_small_null_keeps_degrees_and_weights_but_not_partners() -> None:
    real = small().connectome
    check_null(real, shuffled(real, seed=1))


def test_same_seed_same_null_brain_different_seed_different() -> None:
    real = small().connectome
    assert shuffled(real, 4).fingerprint == shuffled(real, 4).fingerprint
    assert shuffled(real, 4).fingerprint != shuffled(real, 5).fingerprint
    assert shuffled(real, 4).fingerprint != real.fingerprint


@pytest.mark.skipif(not HAVE_DATA, reason="FlyWire data not downloaded")
def test_full_null_brain() -> None:
    from tramlines.brain.connectome import load_connectome

    real = load_connectome()
    check_null(real, shuffled(real, seed=0))


def test_partial_null_rewires_only_the_chosen_fraction() -> None:
    real = small().connectome
    null = shuffled(real, seed=2, fraction=0.1)
    _, post, _ = edges(real)
    null_pre, null_post, _ = edges(null)
    n = real.n_neurons
    assert np.array_equal(np.bincount(null_post, minlength=n), np.bincount(post, minlength=n))
    assert not (null_pre == null_post).any()
    assert len(np.unique(null_pre * n + null_post)) == len(null_post)
    moved = (null_post != post).mean()
    assert 0.05 < moved <= 0.1  # a few chosen connections draw their own receiver back
