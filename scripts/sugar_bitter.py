"""Does bitter taste suppress feeding? Sugar held at 150 Hz, bitter swept (ADR-0027).

uv run python scripts/sugar_bitter.py
"""

from __future__ import annotations

import csv
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import torch

from tramlines.brain.connectome import Connectome, load_connectome
from tramlines.brain.engine import Brain, enable_determinism
from tramlines.brain.neurons import REFERENCE_SUGAR_GRNS, load_catalog

OUT = Path(__file__).resolve().parent.parent / "docs" / "assets" / "sugar_bitter.csv"
SUGAR_HZ = 150.0
BITTER_HZ = (0.0, 50.0, 100.0, 150.0, 200.0)
SEEDS = range(5)

_connectome: Connectome | None = None


def trial(job: tuple[float, int]) -> tuple[float, int, list[int]]:
    global _connectome
    bitter_hz, seed = job
    enable_determinism()
    if _connectome is None:
        _connectome = load_connectome()
    catalog = load_catalog()
    sugar = list(REFERENCE_SUGAR_GRNS)
    bitter = catalog.find(cell_class="gustatory", cell_sub_class="bitter")
    brain = Brain(_connectome, catalog.index_of(sugar + bitter), seed=seed)
    rates = torch.tensor([SUGAR_HZ] * len(sugar) + [bitter_hz] * len(bitter), dtype=torch.float64)
    brain.set_input_rates(rates)
    record = brain.run(10_000)
    mn9 = catalog.index_of(catalog.find(cell_type="CB0701"))  # left, right
    return bitter_hz, seed, [record.count(int(i)) for i in mn9]


def main() -> None:
    results: dict[float, list[list[int]]] = {b: [] for b in BITTER_HZ}
    with ProcessPoolExecutor(max_workers=2) as pool:  # memory rule (ADR-0029, ADR-0032)
        for bitter_hz, _seed, counts in pool.map(trial, [(b, s) for b in BITTER_HZ for s in SEEDS]):
            results[bitter_hz].append(counts)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "bitter_hz",
                "sugar_hz",
                "mn9_left_mean",
                "mn9_left_sd",
                "mn9_right_mean",
                "mn9_right_sd",
            ]
        )
        for bitter_hz, trials in results.items():
            t = torch.tensor(trials, dtype=torch.float64)
            m, sd = t.mean(0), t.std(0, correction=0)
            writer.writerow(
                [bitter_hz, SUGAR_HZ, *(round(float(x), 1) for x in (m[0], sd[0], m[1], sd[1]))]
            )
    print(OUT.read_text())


if __name__ == "__main__":
    main()
