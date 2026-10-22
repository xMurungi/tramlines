# book: needs-data
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"

neurons = pd.read_csv(DATA / "Completeness_783.csv", index_col=0)
connections = pd.read_parquet(
    DATA / "Connectivity_783.parquet",
    columns=["Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"],
)
annotations = pd.read_csv(
    DATA / "neuron_annotations_v2.1.0.tsv",
    sep="\t",
    usecols=["root_id", "super_class", "cell_type", "side"],
    index_col="root_id",
)

signed = connections["Excitatory x Connectivity"]
print(f"neurons:     {len(neurons):,}")
print(f"connections: {len(connections):,}")
print(f"synapses:    {signed.abs().sum():,}")
print(f"excitatory connections: {(signed > 0).sum():,}")
print(f"inhibitory connections: {(signed < 0).sum():,}")

mn9 = 720575940660219265
about = annotations.loc[mn9]
index = neurons.index.get_loc(mn9)
incoming = connections[connections["Postsynaptic_Index"] == index]
print(f"MN9 is a {about['super_class']} neuron of type {about['cell_type']}, {about['side']} side")
print(f"MN9 is neuron number {index} in the simulation")
print(f"MN9 listens to {len(incoming)} neurons through {incoming['Excitatory x Connectivity'].abs().sum():,} synapses")
