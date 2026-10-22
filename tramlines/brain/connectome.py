"""The wiring as the engine reads it: for each neuron, its outgoing synapses.

Spikes are rare (a few per step among 138,639 neurons), so the engine never
multiplies the whole weight matrix. It looks up only the outgoing synapses of
the neurons that fired. Storing those lists back to back, grouped by sender, is
the CSR layout ("compressed sparse rows") with one row per presynaptic neuron.

A `Connectome` is immutable after it is built: every fork of a brain shares the
same one (ADR-0008). Event-driven delivery is ADR-0018.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import torch

from tramlines.brain.data import COMPLETENESS_FILE, CONNECTIVITY_FILE, DATA_DIR
from tramlines.brain.params import PARAMS, LIFParams


@dataclass(frozen=True)
class Connectome:
    n_neurons: int
    # int64 [n_neurons + 1]: the synapses of neuron j are positions row_start[j]:row_start[j+1]
    row_start: torch.Tensor
    post: torch.Tensor  # int32 [n_connections]: receiving neuron of each connection
    weight_mV: torch.Tensor  # float64 [n_connections]: signed synapse count * w_syn

    @property
    def n_connections(self) -> int:
        return int(self.post.shape[0])

    def outgoing(self, pre: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Receivers and weights of every connection leaving the neurons in `pre`.

        The result is in a fixed order (by sender as given, then by storage order),
        so summing it is deterministic (ADR-0007).
        """
        starts = self.row_start[pre]
        counts = self.row_start[pre + 1] - starts
        # Position of each connection: its sender's start, plus its rank within that sender.
        first_slot = torch.cumsum(counts, 0) - counts
        positions = torch.repeat_interleave(starts - first_slot, counts)
        positions += torch.arange(positions.shape[0], dtype=torch.int64)
        return self.post[positions], self.weight_mV[positions]


def from_arrays(
    n_neurons: int,
    pre: np.ndarray,
    post: np.ndarray,
    signed_synapses: np.ndarray,
    params: LIFParams = PARAMS,
) -> Connectome:
    order = np.argsort(pre, kind="stable")
    counts = np.bincount(pre, minlength=n_neurons)
    row_start = np.concatenate([[0], np.cumsum(counts)]).astype(np.int64)
    return Connectome(
        n_neurons=n_neurons,
        row_start=torch.from_numpy(row_start),
        post=torch.from_numpy(post[order].astype(np.int32)),
        weight_mV=torch.from_numpy(signed_synapses[order].astype(np.float64) * params.w_syn_mV),
    )


def load_connectome(data_dir: Path = DATA_DIR, params: LIFParams = PARAMS) -> Connectome:
    """Read only the three columns the engine needs (the full table peaks at 2.3 GB)."""
    n_neurons = len(pd.read_csv(data_dir / COMPLETENESS_FILE, usecols=[0]))
    table = pq.read_table(
        data_dir / CONNECTIVITY_FILE,
        columns=["Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"],
    )
    return from_arrays(
        n_neurons,
        table.column("Presynaptic_Index").to_numpy(),
        table.column("Postsynaptic_Index").to_numpy(),
        table.column("Excitatory x Connectivity").to_numpy(),
        params,
    )
