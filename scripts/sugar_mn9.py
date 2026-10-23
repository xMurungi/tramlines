"""Phase 1 acceptance experiment (CLAUDE.md section 7.3): sugar GRNs drive MN9.

Stimulates the sugar gustatory receptor neurons at a range of rates and records
how fast MN9 (the proboscis motor neuron) fires. Each trial is 1 s of simulated
time with its own seed. Writes a CSV of results and the plot used in The Book.

    uv run python scripts/sugar_mn9.py                          # reference 21 GRNs
    uv run python scripts/sugar_mn9.py --set annotated --tag annotated
    uv run python scripts/sugar_mn9.py --replot                 # redraw from the saved CSV
"""

from __future__ import annotations

import argparse
import csv
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import torch

from tramlines.brain.connectome import Connectome, load_connectome
from tramlines.brain.engine import Brain, enable_determinism
from tramlines.brain.neurons import (
    MN9_CELL_TYPE,
    REFERENCE_MN9,
    REFERENCE_SUGAR_GRNS,
    load_catalog,
)

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
RATES_HZ = (0, 10, 20, 30, 40, 50, 60, 80, 100, 120, 150, 200)
STEPS_PER_TRIAL = 10_000  # 1 s at dt = 0.1 ms

_connectome: Connectome | None = None


def sugar_set(name: str) -> list[int]:
    if name == "reference":
        return list(REFERENCE_SUGAR_GRNS)
    # All sugar/water GRNs entering on the same side as the reference set (ADR-0017).
    return load_catalog().find(cell_class="gustatory", cell_sub_class="sugar/water", side="left")


def run_trial(job: tuple[list[int], list[int], float, int]) -> tuple[float, int, list[int], float]:
    global _connectome
    sugar, readout, rate, seed = job
    enable_determinism(threads=1)
    if _connectome is None:
        _connectome = load_connectome()
    catalog = load_catalog()
    brain = Brain(_connectome, catalog.index_of(sugar), seed=seed)
    brain.set_input_rates(rate)
    start = time.perf_counter()
    record = brain.run(STEPS_PER_TRIAL)
    wall = time.perf_counter() - start
    counts = [record.count(int(i)) for i in catalog.index_of(readout)]
    return rate, seed, counts, wall


def plot(rows: list[dict[str, float]], labels: list[str], out: Path, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    surface, ink, muted, grid = "#07070a", "#e9e3d6", "#8a8478", "#24222a"
    colors = ["#bb861f", "#3a9fc4"]  # validated pair on the dark surface (ADR-0019)
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=160, facecolor=surface)
    ax.set_facecolor(surface)
    rates = [r["rate_hz"] for r in rows]
    for k, (label, color) in enumerate(zip(labels, colors, strict=False)):
        mean = [r[f"mean_{k}"] for r in rows]
        sd = [r[f"sd_{k}"] for r in rows]
        ax.fill_between(
            rates,
            [m - s for m, s in zip(mean, sd, strict=True)],
            [m + s for m, s in zip(mean, sd, strict=True)],
            color=color,
            alpha=0.18,
            linewidth=0,
        )
        ax.plot(rates, mean, color=color, linewidth=2, marker="o", markersize=4, label=label)
        ax.annotate(
            label.split(" (")[0],
            (rates[-1], mean[-1]),
            xytext=(6, 0),
            textcoords="offset points",
            va="center",
            color=ink,
            fontsize=8,
        )
    ax.set_xlabel("Sugar GRN stimulation rate (Hz)", color=muted)
    ax.set_ylabel("Motor neuron firing rate (Hz)", color=muted)
    ax.set_title(title, color=ink, fontsize=11, loc="left")
    ax.tick_params(colors=muted)
    ax.grid(color=grid, linewidth=0.6)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(left=0, right=max(rates) * 1.12)
    ax.set_ylim(bottom=0)
    legend = ax.legend(frameon=False, loc="upper left", fontsize=8)
    for text in legend.get_texts():
        text.set_color(ink)
    fig.tight_layout()
    fig.savefig(out, facecolor=surface)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--set", choices=["reference", "annotated"], default="reference")
    parser.add_argument("--trials", type=int, default=10)
    parser.add_argument("--workers", type=int, default=2)  # memory rule (ADR-0029, ADR-0032)
    parser.add_argument("--rates", type=float, nargs="*", default=list(RATES_HZ))
    parser.add_argument("--tag", default="reference")
    parser.add_argument("--replot", action="store_true", help="redraw from the saved CSV only")
    args = parser.parse_args()

    catalog = load_catalog()
    sugar = sugar_set(args.set)
    # Reference MN9 first, then its partner of the same cell type on the other side.
    partners = [r for r in catalog.find(cell_type=MN9_CELL_TYPE) if r != REFERENCE_MN9]
    readout = [REFERENCE_MN9, *partners]
    sides = [str(catalog.annotations.loc[r, "side"]) for r in readout]
    labels = [f"MN9, {sides[0]} (reference ID)"] + [f"MN9, {s}" for s in sides[1:]]
    csv_path = ASSETS / f"sugar_mn9_{args.tag}.csv"
    if args.replot:
        with csv_path.open() as f:
            rows = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]
        trials = int(rows[0]["trials"])
        title = f"Sugar → MN9: {len(sugar)} sugar GRNs, {trials} trials per rate (mean ± SD)"
        plot(rows, labels, csv_path.with_suffix(".png"), title)
        return
    print(f"stimulating {len(sugar)} sugar GRNs; reading {readout}")

    jobs = [(sugar, readout, rate, seed) for rate in args.rates for seed in range(args.trials)]
    results: dict[float, list[list[int]]] = {r: [] for r in args.rates}
    walls: list[float] = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for rate, _seed, counts, wall in pool.map(run_trial, jobs):
            results[rate].append(counts)
            walls.append(wall)
            print(f"  {rate:6.1f} Hz seed {_seed}: MN9 {counts}  ({wall:.1f} s)", flush=True)

    rows = []
    for rate in args.rates:
        trials = torch.tensor(results[rate], dtype=torch.float64)  # [trials, readouts], Hz
        row: dict[str, float] = {"rate_hz": rate, "trials": float(len(trials))}
        for k in range(len(readout)):
            row[f"mean_{k}"] = float(trials[:, k].mean())
            row[f"sd_{k}"] = float(trials[:, k].std(correction=0))
        rows.append(row)

    ASSETS.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    title = f"Sugar → MN9: {len(sugar)} sugar GRNs, {args.trials} trials per rate (mean ± SD)"
    plot(rows, labels, csv_path.with_suffix(".png"), title)
    print(f"mean wall-clock per simulated second: {sum(walls) / len(walls):.2f} s")


if __name__ == "__main__":
    main()
