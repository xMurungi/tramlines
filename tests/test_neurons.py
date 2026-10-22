"""The reference neuron sets are what their annotations say they are (ADR-0017)."""

import pytest

from tramlines.brain.data import DATA_DIR
from tramlines.brain.neurons import (
    ANNOTATIONS_FILE,
    MN9_CELL_TYPE,
    REFERENCE_MN9,
    REFERENCE_SUGAR_GRNS,
    load_catalog,
)

pytestmark = [
    pytest.mark.data,
    pytest.mark.skipif(
        not (DATA_DIR / ANNOTATIONS_FILE).exists(),
        reason="run `uv run python scripts/fetch_data.py` first",
    ),
]


def test_reference_sugar_grns_are_annotated_sugar_grns() -> None:
    catalog = load_catalog()
    rows = catalog.annotations.loc[list(REFERENCE_SUGAR_GRNS)]
    assert len(set(REFERENCE_SUGAR_GRNS)) == 21
    assert (rows["cell_class"] == "gustatory").all()
    assert (rows["cell_sub_class"] == "sugar/water").all()
    assert rows["side"].nunique() == 1
    assert len(catalog.index_of(REFERENCE_SUGAR_GRNS)) == 21


def test_reference_mn9_is_cb0701_motor_neuron() -> None:
    catalog = load_catalog()
    row = catalog.annotations.loc[REFERENCE_MN9]
    assert row["super_class"] == "motor"
    assert row["cell_type"] == MN9_CELL_TYPE
    assert REFERENCE_MN9 in catalog.find(cell_type=MN9_CELL_TYPE)


def test_index_of_rejects_unknown_ids() -> None:
    with pytest.raises(KeyError):
        load_catalog().index_of([1234])
