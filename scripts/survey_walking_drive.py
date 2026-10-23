"""Which neurons upstream of P9 make a good walking drive? (ADR-0036)

P9 (DNp09) is the forward-speed readout, so it must not also be driven (ADR-0035).
For each candidate type that excites P9, stimulate it for 1 s and measure how hard
P9 fires, what else it drives, and how much of the brain it wakes (which sets speed).

    uv run python scripts/survey_walking_drive.py
"""

from __future__ import annotations

import csv
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from tramlines.brain.connectome import Connectome, load_connectome
from tramlines.brain.engine import Brain, enable_determinism
from tramlines.brain.neurons import NeuronCatalog, load_catalog
from tramlines.world.decoder import FlyDecoder

OUT = Path(__file__).resolve().parent.parent / "docs" / "assets" / "walking_drive_survey.csv"
CANDIDATES = ("CL270", "PVLP150", "AVLP369", "PVLP076", "CB2777", "CB2659", "CB2458", "CB1446")
RATES_HZ = (100.0,)
# Second round: the cleanest candidate alone and paired, at rising drive rates.
DOSE = (("CB2777",), ("CB2777", "AVLP369"), ("CB2777", "CB2659"))
DOSE_RATES_HZ = (100.0, 150.0, 200.0)
SEEDS = (0, 1)
STEPS = 10_000

_connectome: Connectome | None = None


def neurons_of(catalog: NeuronCatalog, name: str) -> list[int]:
    by_hemibrain = catalog.find(hemibrain_type=name)
    return by_hemibrain or catalog.find(cell_type=name)


def trial(job: tuple[str, float, int]) -> dict[str, object]:
    global _connectome
    name, rate, seed = job
    enable_determinism()
    if _connectome is None:
        _connectome = load_connectome()
    catalog = load_catalog()
    drive = [n for part in name.split("+") for n in neurons_of(catalog, part)]
    brain = Brain(_connectome, catalog.index_of(drive), seed=seed)
    brain.set_input_rates(rate)
    record = brain.run(STEPS)
    readouts = FlyDecoder.from_catalog(catalog).readout_neurons.tolist()
    counts = [record.count(int(n)) for n in readouts]
    overlap = sorted(set(catalog.index_of(drive).tolist()) & set(readouts))
    return {
        "type": name,
        "neurons": len(drive),
        "rate_hz": rate,
        "seed": seed,
        "p9_mean_hz": sum(counts[0:4]) / 4,
        "dna02_left_hz": counts[4],
        "dna02_right_hz": counts[5],
        "mdn_mean_hz": sum(counts[6:10]) / 4,
        "gf_max_hz": max(counts[10:12]),
        "mn9_max_hz": max(counts[12:14]),
        "awake_neurons": int(brain.awake_neurons().numel()),
        "total_spikes": int(record.neurons.numel()),
        "overlaps_readout": len(overlap),
    }


def main() -> None:
    import sys

    if sys.argv[1:] == ["--dose"]:
        names = ["+".join(combo) for combo in DOSE]
        jobs = [(n, r, seed) for n in names for r in DOSE_RATES_HZ for seed in SEEDS]
        with ProcessPoolExecutor(max_workers=2) as pool:
            rows = list(pool.map(trial, jobs))
        for n in names:
            for r in DOSE_RATES_HZ:
                mine = [x for x in rows if x["type"] == n and x["rate_hz"] == r]
                p9 = [float(str(x["p9_mean_hz"])) for x in mine]
                side = max(float(str(x["gf_max_hz"])) for x in mine)
                awake = sum(int(str(x["awake_neurons"])) for x in mine) / len(mine)
                print(
                    f"{n:16} {r:5.0f} Hz: P9 {min(p9):5.1f}-{max(p9):5.1f} Hz"
                    f"  GF {side:3.0f}  awake {awake:6.0f}"
                )
        return
    jobs = [(name, rate, seed) for name in CANDIDATES for rate in RATES_HZ for seed in SEEDS]
    with ProcessPoolExecutor(max_workers=2) as pool:  # memory rule (ADR-0029, ADR-0032)
        rows = list(pool.map(trial, jobs))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    header = ("type", "n", "P9 Hz", "DNa02 L/R", "MDN", "GF", "MN9", "awake", "overlap")
    print(*header)
    for name in CANDIDATES:
        mine = [r for r in rows if r["type"] == name]

        def mean(k: str, mine: list[dict[str, object]] = mine) -> float:
            return sum(float(str(r[k])) for r in mine) / len(mine)

        print(
            f"{name:8} {mine[0]['neurons']:>3} {mean('p9_mean_hz'):7.1f} "
            f"{mean('dna02_left_hz'):4.0f}/{mean('dna02_right_hz'):<4.0f} "
            f"{mean('mdn_mean_hz'):5.1f} "
            f"{mean('gf_max_hz'):5.0f} {mean('mn9_max_hz'):5.0f} {mean('awake_neurons'):7.0f} "
            f"{mine[0]['overlaps_readout']:>7}"
        )


if __name__ == "__main__":
    main()
