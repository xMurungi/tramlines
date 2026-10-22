"""Scientific regression: sugar on the tongue drives MN9 (CLAUDE.md 7.3, ADR-0020).

Two layers. The golden test pins one seed exactly and runs on every change. The band
test checks the published shape (silent at low rates, strong at high rates) over
several seeds; it takes a few minutes, so it is marked `slow`.
"""

import pytest

from tramlines.brain.connectome import Connectome, load_connectome
from tramlines.brain.data import DATA_DIR
from tramlines.brain.engine import Brain, enable_determinism
from tramlines.brain.neurons import (
    ANNOTATIONS_FILE,
    REFERENCE_MN9,
    REFERENCE_SUGAR_GRNS,
    NeuronCatalog,
    load_catalog,
)

pytestmark = [
    pytest.mark.data,
    pytest.mark.skipif(
        not (DATA_DIR / ANNOTATIONS_FILE).exists(),
        reason="run `uv run python scripts/fetch_data.py` first",
    ),
]

ONE_SECOND = 10_000
Setup = tuple[Connectome, NeuronCatalog]

# ADR-0020: mean MN9 rate over seeds 0-4, in Hz, must fall inside these bands.
BANDS_HZ = {20.0: (0.0, 1.0), 60.0: (25.0, 50.0), 200.0: (80.0, 105.0)}


@pytest.fixture(scope="module")
def setup() -> Setup:
    enable_determinism()
    return load_connectome(), load_catalog()


def mn9_spikes(setup: Setup, rate_hz: float, seed: int, steps: int) -> int:
    connectome, catalog = setup
    brain = Brain(connectome, catalog.index_of(REFERENCE_SUGAR_GRNS), seed=seed)
    brain.set_input_rates(rate_hz)
    record = brain.run(steps)
    return record.count(int(catalog.index_of([REFERENCE_MN9])[0]))


def test_silent_without_sugar(setup: Setup) -> None:
    connectome, catalog = setup
    brain = Brain(connectome, catalog.index_of(REFERENCE_SUGAR_GRNS), seed=0)
    assert brain.run(2000).neurons.numel() == 0  # no input, no spikes anywhere


def test_golden_seed_0_at_200_hz(setup: Setup) -> None:
    # Exact values for seed 0; also what Chapter 18 of The Book prints.
    assert mn9_spikes(setup, 200.0, seed=0, steps=ONE_SECOND) == 98


@pytest.mark.slow
@pytest.mark.parametrize("rate_hz", sorted(BANDS_HZ))
def test_mn9_rate_bands(setup: Setup, rate_hz: float) -> None:
    rates = [mn9_spikes(setup, rate_hz, seed, ONE_SECOND) for seed in range(5)]
    low, high = BANDS_HZ[rate_hz]
    assert low <= sum(rates) / len(rates) <= high, rates
