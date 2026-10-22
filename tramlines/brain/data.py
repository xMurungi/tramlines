"""Load the FlyWire v783 neuron list and connectivity table.

Phase 0 scope: read the two files, check they agree with each other, and report
their size. Building the weight tensors for the engine comes in Phase 1.

The neuron's *index* (its row in the completeness file) is the address the
simulator uses. The FlyWire *root ID* is the address the scientific world uses.
The connectivity file carries both, and `load_brain` checks they match.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
COMPLETENESS_FILE = "Completeness_783.csv"
CONNECTIVITY_FILE = "Connectivity_783.parquet"

CONNECTIVITY_COLUMNS = (
    "Presynaptic_ID",
    "Postsynaptic_ID",
    "Presynaptic_Index",
    "Postsynaptic_Index",
    "Connectivity",  # synapse count, always >= 1
    "Excitatory",  # +1 excitatory, -1 inhibitory (predicted transmitter)
    "Excitatory x Connectivity",  # signed synapse count: W_ij in CLAUDE.md section 7.2
)


@dataclass(frozen=True)
class RawBrain:
    """The two v783 tables, validated, before any simulation structure is built."""

    root_ids: np.ndarray  # int64, one per neuron; position = simulator index
    connections: pd.DataFrame  # one row per (pre, post) pair, columns as above

    @property
    def n_neurons(self) -> int:
        return int(self.root_ids.shape[0])

    @property
    def n_connections(self) -> int:
        return len(self.connections)

    @property
    def n_synapses(self) -> int:
        return int(self.connections["Connectivity"].sum())


def load_brain(data_dir: Path = DATA_DIR) -> RawBrain:
    completeness = pd.read_csv(data_dir / COMPLETENESS_FILE, index_col=0)
    connections = pd.read_parquet(data_dir / CONNECTIVITY_FILE)

    missing = set(CONNECTIVITY_COLUMNS) - set(connections.columns)
    if missing:
        raise ValueError(f"connectivity file lacks columns: {sorted(missing)}")

    root_ids = completeness.index.to_numpy(dtype=np.int64)
    _check_indices_match_ids(root_ids, connections)
    return RawBrain(root_ids=root_ids, connections=connections)


def _check_indices_match_ids(root_ids: np.ndarray, connections: pd.DataFrame) -> None:
    """Index and root ID must name the same neuron, or every lookup is silently wrong."""
    for side in ("Presynaptic", "Postsynaptic"):
        index = connections[f"{side}_Index"].to_numpy()
        ids = connections[f"{side}_ID"].to_numpy()
        if not np.array_equal(root_ids[index], ids):
            raise ValueError(f"{side} index and root ID columns disagree")


def main() -> None:
    brain = load_brain()
    print(f"neurons: {brain.n_neurons:,}, connections: {brain.n_connections:,}")
    print(f"synapses: {brain.n_synapses:,}")


if __name__ == "__main__":
    main()
