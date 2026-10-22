"""Does one extra spike change the fly's future? (ADR-0029)

At two moments of the seed-0 headless run (walking at 0.5 s; feeding at 4.0 s, with
the shadow due at 6 s), the timeline is copied 16 times. Each copy gets one extra
spike in a different, randomly chosen neuron, then all run 3 s ahead. We measure
how far each fly ends up from the untouched one, and how its brain differs.

    uv run python scripts/divergence_study.py                 # any neuron
    uv run python scripts/divergence_study.py --pick awake    # a neuron already active
    uv run python scripts/divergence_study.py --pick inputs   # a sensory / drive neuron
    uv run python scripts/divergence_study.py --arena decision --pick driven \
        --moments laced=1300 shadow=3100                      # aimed, at decision points
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
from tramlines.world.arena import DECISION_ARENA, DEFAULT_ARENA, Arena
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
ARENAS = {"default": DEFAULT_ARENA, "decision": DECISION_ARENA}


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


def load(path: Path, arena: Arena) -> Timeline:
    connectome, _, senses, decoder = parts()
    return Timeline.load(path, connectome, arena, senses, decoder)


def run_branch(
    job: tuple[str, Path, int | None, str],
) -> tuple[str, int | None, list[Pose], list[int]]:
    """Load the moment, inject one spike (None = the untouched future), run ahead."""
    moment, path, neuron, arena_name = job
    timeline = load(path, ARENAS[arena_name])
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


def plot_fan(
    base: list[Pose], branches: list[list[Pose]], arena: Arena, out: Path, title: str
) -> None:
    """The fan: the untouched future in gold, each one-spike future in blue."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    surface, ink, muted = "#07070a", "#e9e3d6", "#8a8478"
    gold, blue = "#bb861f", "#3a9fc4"  # validated pair on the dark surface (ADR-0019)
    fig, ax = plt.subplots(figsize=(6.4, 6.4), dpi=160, facecolor=surface)
    ax.set_facecolor(surface)
    for patch in arena.patches:
        ax.add_patch(Circle((patch.x_mm, patch.y_mm), patch.radius_mm, fill=False, color=muted,
                            ls="-" if patch.kind == "food" else "--", linewidth=1))  # fmt: skip
    feed_labelled = False
    for i, poses in enumerate(branches):
        label = f"{len(branches)} futures, each one extra spike" if i == 0 else None
        xs, ys = [p.x_mm for p in poses], [p.y_mm for p in poses]
        ax.plot(xs, ys, color=blue, linewidth=1, alpha=0.75, label=label)
        fed = [p for p in poses if p.feeding]
        if fed:
            feed_label = None if feed_labelled else "stops to feed"
            ax.plot(fed[0].x_mm, fed[0].y_mm, "s", color=ink, markersize=4, label=feed_label)
            feed_labelled = True
    ax.plot([p.x_mm for p in base], [p.y_mm for p in base], color=gold, linewidth=2.2,
            label="the untouched future")  # fmt: skip
    ax.plot(base[0].x_mm, base[0].y_mm, "o", color=gold, markersize=6)
    xs = [p.x_mm for poses in [base, *branches] for p in poses]
    ys = [p.y_mm for poses in [base, *branches] for p in poses]
    pad = 3.0
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)
    ax.set_aspect("equal")
    ax.axis("off")
    legend = ax.legend(frameon=False, loc="lower left", fontsize=8)
    for text in legend.get_texts():
        text.set_color(ink)
    ax.set_title(title, color=ink, fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(out, facecolor=surface)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pick", choices=["random", "awake", "inputs", "driven"], default="random")
    parser.add_argument("--arena", choices=list(ARENAS), default="default")
    parser.add_argument("--moments", nargs="*", default=[f"{k}={v}" for k, v in MOMENTS_MS.items()])
    parser.add_argument("--workers", type=int, default=4)  # memory headroom (monitoring)
    args = parser.parse_args()
    connectome, catalog, senses, decoder = parts()
    arena = ARENAS[args.arena]
    moments = {name: int(ms) for name, ms in (m.split("=") for m in args.moments)}
    n = connectome.n_neurons
    workdir = Path(tempfile.mkdtemp())
    jobs: list[tuple[str, Path, int | None, str]] = []
    timeline = Timeline(connectome, arena, senses, decoder, seed=0, start=DEFAULT_START)
    for moment, at_ms in moments.items():
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
            # receiving input right now (ADR-0031): the senses' current rates
            "driven": timeline.brain.input_neurons[senses.rates_hz(timeline.fly, arena) > 0],
        }[args.pick]
        chosen: list[int] = []
        while len(chosen) < BRANCHES:
            k = int(pool_of[int(torch.randint(len(pool_of), (1,), generator=chooser))])
            if just_now - int(last[k]) >= int(refractory[k]) and k not in chosen:
                chosen.append(k)
        jobs += [(moment, path, None, args.arena)] + [(moment, path, k, args.arena) for k in chosen]

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
        start_bin = (moments[moment] * 10) // BIN_STEPS
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
    for moment, at_ms in moments.items():
        base_poses = base[moment][0]
        branches = [poses for m, k, poses, _ in results if m == moment and k is not None]
        plot_fan(
            base_poses, branches, arena,
            ASSETS / f"fan_{args.arena}_{args.pick}_{moment}.png",
            f"One extra spike, 16 times, at {at_ms / 1000:g} s ({moment}): 3 s of futures",
        )  # fmt: skip
    out = ASSETS / f"divergence_{args.arena}_{args.pick}.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for moment in moments:
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
