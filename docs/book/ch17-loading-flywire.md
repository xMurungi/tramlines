# Chapter 17 — Loading FlyWire v783

> 138,639 neurons, traced by hand and machine from one fly's brain, are about to arrive on your disk. How do you know they arrived intact?

## Where we are
You can store huge sparse tables and do maths on them with PyTorch. This chapter downloads the real fly brain, checks it, and asks it its first questions.

## The idea
The FlyWire data comes as three files:

- a **neuron list**: one row per neuron, giving its [root ID](glossary.md);
- a **connectivity table**: one row per connected pair of neurons, with how many synapses join them and whether the connection excites or inhibits;
- an **annotation table**: what scientists call each neuron (its class, type, side of the brain).

The row number of a neuron in the neuron list becomes its address in our simulation, its *index*. The root ID is its address in the scientific world. You need both, and they must never get out of step.

Before trusting a download, you check its **fingerprint**. A [hash](glossary.md) is a short code computed from every byte of a file. Change one byte anywhere and the hash changes completely. If your hash matches the one published with the data, you have exactly the bytes everyone else used. It is like checking the seal on a jar.

## Build it

1. **Download the data.** In the project, run:

    ```bash
    uv run python scripts/fetch_data.py
    ```

    This fetches about 130 MB from two pinned sources ([ADR-0013](../decisions/0013-data-files-and-source.md), [ADR-0017](../decisions/0017-annotations-and-neuron-sets.md)) and refuses any file whose fingerprint is wrong. In your own book folder, make a `data` folder next to your chapter folders and put the three files in it.

2. **Check the fingerprints yourself.** Save as `ch17/fingerprint.py`:

    ```python
    import hashlib
    from pathlib import Path

    DATA = Path(__file__).resolve().parent.parent / "data"

    for name in ["Completeness_783.csv", "Connectivity_783.parquet"]:
        contents = (DATA / name).read_bytes()
        fingerprint = hashlib.sha256(contents).hexdigest()
        print(f"{name}: {len(contents):,} bytes, sha256 {fingerprint[:16]}...")
    ```

3. **Ask the brain some questions.** Save as `ch17/load_flywire.py`:

    ```python
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
    ```

## Run it

```bash
uv run python ch17/fingerprint.py
uv run python ch17/load_flywire.py
```

```text
Completeness_783.csv: 3,327,347 bytes, sha256 bbb847a4cc2caaa7...
Connectivity_783.parquet: 100,804,642 bytes, sha256 efeb23fb99098e9c...
```

```text
neurons:     138,639
connections: 15,091,983
synapses:    54,492,922
excitatory connections: 9,059,302
inhibitory connections: 6,032,681
MN9 is a motor neuron of type CB0701, right side
MN9 is neuron number 138332 in the simulation
MN9 listens to 227 neurons through 5,579 synapses
```

## The click
Those numbers are a brain. Not a model of one invented by a programmer: a measured one. Every one of those 54 million synapses was found in electron-microscope images of a real fly, and a person checked the neurons they belong to.

Notice the column called `Excitatory x Connectivity`. It is the synapse count with a sign: positive if the sending neuron's transmitter excites, negative if it inhibits. That single signed number per connection is the entire wiring the simulation uses. The next chapter turns it into electricity.

And notice MN9. It has no label saying "MN9". Scientists named it in a paper; the annotation table calls it by a type code, CB0701. Matching the names of the literature to the names of a dataset is real, careful work, and we wrote down how we did it ([ADR-0017](../decisions/0017-annotations-and-neuron-sets.md)).

## Break it

1. Change one character in a copy of `Completeness_783.csv` and fingerprint the copy. How much of the hash changes?
2. Count how many connections have more than 100 synapses. Are they mostly excitatory or inhibitory?
3. Find MN9's partner on the other side: filter `annotations` for `cell_type == "CB0701"`.
4. Which neuron *sends* the most connections? (Hint: `value_counts()` on `Presynaptic_Index`.)

## When it goes wrong

- **`FileNotFoundError`.** The `data` folder is not where the program looks: next to your chapter folders. Print `DATA` to see the path it expects.
- **`ImportError: Unable to find a usable engine ... parquet`.** Install the parquet reader: `uv add pyarrow`.
- **`KeyError: 720575940660219265`.** You are using annotations from a different FlyWire version. IDs change between versions; use release v2.1.0.

## Check yourself

1. What is the difference between a neuron's root ID and its index?
2. Why check a hash after downloading?
3. What does a negative value in `Excitatory x Connectivity` mean?
4. Why does MN9 appear as "CB0701" in the annotations?

??? note "Answers"
    1. The root ID names the neuron in FlyWire; the index is its row number, its address in our simulation.
    2. To prove the file is exactly, byte for byte, the file everyone else uses.
    3. The connection inhibits: its synapses push the receiving neuron away from firing. The size is the number of synapses.
    4. The dataset and the paper use different naming schemes. The paper's name "MN9" corresponds to the dataset's type CB0701.

## Decisions in this chapter

- [ADR-0002: FlyWire v783](../decisions/0002-dataset-flywire-v783.md)
- [ADR-0013: where the files come from](../decisions/0013-data-files-and-source.md)
- [ADR-0017: annotations and named neurons](../decisions/0017-annotations-and-neuron-sets.md)

## Next
You have the wiring; in Chapter 18 you will run electricity through it, and a fly will taste sugar.
