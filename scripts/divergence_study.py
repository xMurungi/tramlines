"""Does one extra spike change the fly's future? (ADR-0029)

At two moments of the seed-0 headless run (walking at 0.5 s; feeding at 4.0 s, with
the shadow due at 6 s), the timeline is copied 16 times. Each copy gets one extra
spike in a different, randomly chosen neuron, then all run 3 s ahead. We measure
how far each fly ends up from the untouched one, and how its brain differs.

    uv run python scripts/divergence_study.py                 # any neuron
    uv run python scripts/divergence_study.py --pick awake    # a neuron already active
    uv run python scripts/divergence_study.py --pick inputs   # a sensory / drive neuron
"""

from __future__ import annotations

import argparse
import csv
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import torch

from tramlines.brain.connectome import Connectome, load_connectome
from tramlines.brain.engine import SpikeRecord, enable_determinism
from tramlines.brain.neurons import NeuronCatalog, load_catalog
from tramlines.timeline.divergence import first_divergence_ms, path_distance_mm, spike_differences
from tramlines.timeline.timeline import Pose, Timeline
from tramlines.world.arena import DEFAULT_ARENA
from tramlines.world.decoder import FlyDecoder
from tramlines.world.fly import DEFAULT_START
from tramlines.world.senses import FlySenses

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
MOMENTS_MS = {"walking": 500, "feeding": 4000}
BRANCHES = 16
HORIZON_MS = 3000
EPSILON_MM = 0.1  # "the flies are visibly in different places"
BIN_STEPS = 1000  # spike differences counted per 100 ms

_parts: tuple[Connectome, NeuronCatalog, FlySenses, FlyDecoder] | None = None


def parts() -> tuple[Connectome, NeuronCatalog, FlySenses, FlyDecoder]:
    global _parts
    if _parts is None:
        enable_determinism()
        catalog = load_catalog()
        _parts = (
            load_connectome(),
            catalog,
            FlySenses.from_catalog(catalog),
            FlyDecoder.from_catalog(catalog),
        )
    return _parts


def load(path: Path) -> Timeline:
    connectome, _, senses, decoder = parts()
    return Timeline.load(path, connectome, DEFAULT_ARENA, senses, decoder)


def run_branch(job: tuple[str, Path, int | None]) -> tuple[str, int | None, list[Pose], list[int]]:
    """Load the moment, inject one spike (None = the untouched future), run ahead."""
    moment, path, neuron = job
    timeline = load(path)
    if neuron is not None:
        timeline.brain.inject_spike(neuron)
    poses, spikes = timeline.run_recording(HORIZON_MS)
    keys = (spikes.steps * timeline.brain.connectome.n_neurons + spikes.neurons).tolist()
    return moment, neuron, poses, keys


def events(poses: list[Pose]) -> str:
    out, feeding = [], poses[0].feeding
    for p in poses:
        if p.jumped:
            out.append(f"jump {p.time_ms / 1000:.3f}")
        if p.feeding != feeding:
            out.append(f"{'feed' if p.feeding else 'stop'} {p.time_ms / 1000:.3f}")
            feeding = p.feeding
    return "; ".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pick", choices=["random", "awake", "inputs"], default="random")
    parser.add_argument("--workers", type=int, default=4)  # memory headroom (monitoring)
    args = parser.parse_args()
    connectome, catalog, senses, decoder = parts()
    n = connectome.n_neurons
    workdir = Path(tempfile.mkdtemp())
    jobs: list[tuple[str, Path, int | None]] = []
    timeline = Timeline(connectome, DEFAULT_ARENA, senses, decoder, seed=0, start=DEFAULT_START)
    for moment, at_ms in MOMENTS_MS.items():
        timeline.run(at_ms - timeline.fly.time_ms)
        path = workdir / f"{moment}.pt"
        timeline.save(path)
        # Random neurons, the same list every time (its own seeded generator).
        chooser = torch.Generator().manual_seed(at_ms)
        last, refractory = timeline.brain.state.last_spike_step, timeline.brain.refractory_steps
        just_now = timeline.brain.state.step - 1
        pool_of = {
            "random": torch.arange(n),
            "awake": timeline.brain.awake_neurons(),
            "inputs": timeline.brain.input_neurons,
        }[args.pick]
        chosen: list[int] = []
        while len(chosen) < BRANCHES:
            k = int(pool_of[int(torch.randint(len(pool_of), (1,), generator=chooser))])
            if just_now - int(last[k]) >= int(refractory[k]) and k not in chosen:
                chosen.append(k)
        jobs += [(moment, path, None)] + [(moment, path, k) for k in chosen]

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(run_branch, jobs))

    base = {m: (poses, keys) for m, neuron, poses, keys in results if neuron is None}
    rows = []
    for moment, neuron, poses, keys in results:
        if neuron is None:
            continue
        base_poses, base_keys = base[moment]
        dist = path_distance_mm(poses, base_poses)
        ka, kb = torch.tensor(keys, dtype=torch.int64), torch.tensor(base_keys, dtype=torch.int64)
        diffs = spike_differences(
            SpikeRecord(ka // n, ka % n), SpikeRecord(kb // n, kb % n), n, BIN_STEPS
        )
        start_bin = (MOMENTS_MS[moment] * 10) // BIN_STEPS
        diffs = diffs[start_bin:] + [0] * max(0, start_bin + HORIZON_MS // 100 - len(diffs))
        root = int(catalog.root_ids[neuron])
        ann = catalog.annotations.loc[root] if root in catalog.annotations.index else None
        first = first_divergence_ms(dist, EPSILON_MM)
        rows.append(
            {
                "moment": moment,
                "neuron_index": neuron,
                "super_class": "" if ann is None else str(ann["super_class"]),
                "cell_type": "" if ann is None else str(ann["cell_type"]),
                "first_divergence_ms": "" if first is None else first,
                "distance_at_3s_mm": round(dist[-1], 3),
                "max_distance_mm": round(max(dist), 3),
                "spike_diffs_total": sum(diffs),
                "spike_diffs_last_500ms": sum(diffs[-5:]),
                "events": events(poses),
                "base_events": events(base_poses),
                "distance_trace_mm_per_100ms": " ".join(f"{d:.3f}" for d in dist[::100]),
                "spike_diff_trace_per_100ms": " ".join(map(str, diffs[: HORIZON_MS // 100])),
            }
        )
    ASSETS.mkdir(parents=True, exist_ok=True)
    out = ASSETS / f"divergence_{args.pick}.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for moment in MOMENTS_MS:
        mine = [r for r in rows if r["moment"] == moment]
        diverged = [r for r in mine if r["first_divergence_ms"] != ""]
        silent = [r for r in mine if r["spike_diffs_total"] <= 1]
        print(f"{moment}: {len(diverged)}/{len(mine)} paths diverged (> {EPSILON_MM} mm); "
              f"{len(silent)}/{len(mine)} spikes changed nothing else")  # fmt: skip
        for r in mine:
            first = r["first_divergence_ms"]
            print(f"   n{r['neuron_index']:>6} {r['super_class']:>18} first {first!s:>5} ms"
                  f"  end {r['distance_at_3s_mm']:7.3f} mm  spikes {r['spike_diffs_total']:6}"
                  f"  last0.5s {r['spike_diffs_last_500ms']:5}  | {r['events']}")  # fmt: skip
        print(f"   base events: {mine[0]['base_events']}")


if __name__ == "__main__":
    main()
