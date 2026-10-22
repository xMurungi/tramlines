"""From names scientists use (cell types, root IDs) to the engine's neuron indices.

Annotations: FlyWire annotation release v2.1.0, the release matched to v783 (ADR-0017).

The Phase 1 acceptance test uses the neuron sets of the reference code, as CLAUDE.md
section 7.3 allows, and checks every one against the annotations so a stale or
mistyped ID fails loudly (ADR-0017).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from tramlines.brain.data import COMPLETENESS_FILE, DATA_DIR

ANNOTATIONS_FILE = "neuron_annotations_v2.1.0.tsv"
ANNOTATION_COLUMNS = [
    "root_id",
    "super_class",
    "cell_class",
    "cell_sub_class",
    "cell_type",
    "hemibrain_type",  # names from the hemibrain era, e.g. DNp09 (P9), MDN, Giant Fiber
    "side",
    "nerve",
    "top_nt",
]

# The 21 sugar gustatory receptor neurons stimulated in the reference experiment, in the
# v783 version of the list (Eon fly-brain, code/benchmark.py, commit a3db62f9). It is
# Shiu et al.'s example-notebook list with its one v630-only ID replaced. All are
# annotated `gustatory`, `sugar/water`, type LB3, labial nerve (checked in tests).
REFERENCE_SUGAR_GRNS: tuple[int, ...] = (
    720575940624963786,
    720575940630233916,
    720575940637568838,
    720575940638202345,
    720575940617000768,
    720575940630797113,
    720575940632889389,
    720575940621754367,
    720575940621502051,
    720575940640649691,
    720575940639332736,
    720575940616885538,
    720575940639198653,
    720575940639259967,
    720575940617937543,
    720575940632425919,
    720575940633143833,
    720575940612670570,
    720575940628853239,
    720575940629176663,
    720575940611875570,
)

# MN9, the proboscis motor neuron read out in Shiu et al. (example notebook). Its
# annotated cell type is CB0701, a pharyngeal-nerve motor neuron; v2.1.0 has no "MN9" label.
REFERENCE_MN9 = 720575940660219265
MN9_CELL_TYPE = "CB0701"


@dataclass(frozen=True)
class NeuronCatalog:
    root_ids: np.ndarray  # int64; position = engine index
    annotations: pd.DataFrame  # indexed by root_id

    def index_of(self, root_ids: list[int] | tuple[int, ...]) -> torch.Tensor:
        lookup = pd.Index(self.root_ids)
        positions = lookup.get_indexer(list(root_ids))
        if (positions < 0).any():
            missing = [r for r, i in zip(root_ids, positions, strict=True) if i < 0]
            raise KeyError(f"not v783 root IDs in this brain: {missing}")
        return torch.from_numpy(positions.astype(np.int64))

    def find(self, **match: str) -> list[int]:
        """Root IDs whose annotations equal every given column value, in engine order."""
        selected = self.annotations
        for column, value in match.items():
            selected = selected[selected[column] == value]
        positions = pd.Index(self.root_ids).get_indexer(selected.index)
        return [int(r) for r in self.root_ids[np.sort(positions[positions >= 0])]]


def load_catalog(data_dir: Path = DATA_DIR) -> NeuronCatalog:
    root_ids = pd.read_csv(data_dir / COMPLETENESS_FILE, index_col=0).index.to_numpy(np.int64)
    annotations = pd.read_csv(
        data_dir / ANNOTATIONS_FILE, sep="\t", usecols=ANNOTATION_COLUMNS, low_memory=False
    ).set_index("root_id")
    return NeuronCatalog(root_ids=root_ids, annotations=annotations)
