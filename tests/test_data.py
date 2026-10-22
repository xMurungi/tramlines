"""The FlyWire v783 files load and have the shape recorded in data/MANIFEST.md."""

import pytest

from tramlines.brain.data import DATA_DIR, load_brain

pytestmark = [
    pytest.mark.data,
    pytest.mark.skipif(
        not (DATA_DIR / "Connectivity_783.parquet").exists(),
        reason="run `uv run python scripts/fetch_data.py` first",
    ),
]


def test_v783_counts() -> None:
    brain = load_brain()
    assert brain.n_neurons == 138_639
    assert brain.n_connections == 15_091_983
    assert brain.n_synapses == 54_492_922


def test_signs_are_plus_or_minus_one() -> None:
    connections = load_brain().connections
    assert set(connections["Excitatory"].unique()) == {-1, 1}
    signed = connections["Excitatory"] * connections["Connectivity"]
    assert (signed == connections["Excitatory x Connectivity"]).all()
