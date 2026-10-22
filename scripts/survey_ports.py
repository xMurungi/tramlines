"""Survey for the Phase 3 proposals: how hard does each candidate sense drive each
candidate movement neuron? Evidence for the owner's decision (ADR-0023, ADR-0024),
not an implementation of either.

    uv run python scripts/survey_ports.py
"""

from __future__ import annotations

import csv
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from tramlines.brain.connectome import Connectome, load_connectome
from tramlines.brain.engine import Brain, enable_determinism
from tramlines.brain.neurons import REFERENCE_SUGAR_GRNS, NeuronCatalog, load_catalog

OUT = Path(__file__).resolve().parent.parent / "docs" / "assets" / "port_survey.csv"
RATE_HZ = 150.0
SEEDS = (0, 1, 2)
STEPS = 10_000  # 1 s

_connectome: Connectome | None = None


def by_hemibrain_type(catalog: NeuronCatalog, name: str, side: str | None = None) -> list[int]:
    match = {"hemibrain_type": name} if side is None else {"hemibrain_type": name, "side": side}
    return catalog.find(**match)


def stimuli(catalog: NeuronCatalog) -> dict[str, list[int]]:
    ann = catalog.annotations
    jo = ann.index[ann["cell_type"].astype(str).str.match(r"JO-[CE]") & (ann["side"] == "right")]
    in_brain = set(catalog.root_ids.tolist())
    return {
        "none": [],
        "sugar (21 reference GRNs)": list(REFERENCE_SUGAR_GRNS),
        "bitter (42 GRNs)": catalog.find(cell_class="gustatory", cell_sub_class="bitter"),
        "looming right (LC4)": by_hemibrain_type(catalog, "LC4", "right"),
        "looming right (LPLC2)": by_hemibrain_type(catalog, "LPLC2", "right"),
        "wind right (JO-C/E)": [int(r) for r in jo if r in in_brain],
        "walking drive (P9 = DNp09)": by_hemibrain_type(catalog, "DNp09"),
    }


def readouts(catalog: NeuronCatalog) -> dict[str, int]:
    out: dict[str, int] = {}
    for label, name in [
        ("P9/DNp09", "DNp09"),
        ("DNa01", "DNa01"),
        ("DNa02", "DNa02"),
        ("MDN", "MDN"),
        ("GF", "Giant Fiber"),
    ]:
        for side in ("left", "right"):
            for k, root in enumerate(by_hemibrain_type(catalog, name, side)):
                out[f"{label} {side}{'' if k == 0 else f' #{k + 1}'}"] = root
    for side in ("left", "right"):
        out[f"MN9 (CB0701) {side}"] = catalog.find(cell_type="CB0701", side=side)[0]
    return out


def trial(job: tuple[str, list[int], list[int], int]) -> tuple[str, int, list[int]]:
    global _connectome
    name, stimulus, readout, seed = job
    enable_determinism()
    if _connectome is None:
        _connectome = load_connectome()
    catalog = load_catalog()
    brain = Brain(_connectome, catalog.index_of(stimulus), seed=seed)
    brain.set_input_rates(RATE_HZ)
    record = brain.run(STEPS)
    return name, seed, [record.count(int(i)) for i in catalog.index_of(readout)]


def main() -> None:
    catalog = load_catalog()
    stims = stimuli(catalog)
    reads = readouts(catalog)
    for name, ids in stims.items():
        print(f"{name}: {len(ids)} neurons")
    jobs = [(n, s, list(reads.values()), seed) for n, s in stims.items() for seed in SEEDS]
    totals: dict[str, list[int]] = {n: [0] * len(reads) for n in stims}
    with ProcessPoolExecutor(max_workers=5) as pool:
        for name, _seed, counts in pool.map(trial, jobs):
            totals[name] = [a + b for a, b in zip(totals[name], counts, strict=True)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["stimulus (150 Hz)", *reads])
        for name, total in totals.items():
            writer.writerow([name, *[round(t / len(SEEDS), 1) for t in total]])
    print(OUT.read_text())


if __name__ == "__main__":
    main()
