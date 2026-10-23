"""Result 1: how long does a ghost stay right when it knows the brain imperfectly? (ADR-0035)

At three moments of the seed-0 run on the decision dish (walking, on laced food, under
the faint shadow) the true fly is saved. Ghosts start from that save with imperfect
knowledge (perturb.py) and run 3 s ahead next to the truth. The perfect ghost is the
control. For each ghost: when the first spike differs, when the paths separate by
more than 0.1 mm, and what the fly does differently.

    uv run python scripts/horizon_study.py
"""

from __future__ import annotations

import csv
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from tramlines.brain.connectome import Connectome, load_connectome
from tramlines.brain.engine import enable_determinism
from tramlines.brain.neurons import load_catalog
from tramlines.timeline.divergence import first_divergence_ms, path_distance_mm
from tramlines.timeline.perturb import Knowledge, blur
from tramlines.timeline.timeline import Pose, Timeline
from tramlines.world.arena import DECISION_ARENA
from tramlines.world.decoder import FlyDecoder
from tramlines.world.fly import DEFAULT_START
from tramlines.world.senses import FlySenses

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
MOMENTS_MS = {"walking": 500, "laced food": 1200, "shadow": 3350}
HORIZON_MS = 3000
EPSILON_MM = 0.1
KNOWLEDGE: list[Knowledge | None] = [
    None,  # the perfect ghost: the control
    Knowledge("voltage", 1e-12),
    Knowledge("voltage", 1e-9),
    Knowledge("voltage", 1e-6),
    Knowledge("voltage", 1e-3),
    Knowledge("voltage", 1e-2),
    Knowledge("voltage", 1e-1),
    Knowledge("voltage", 1.0),
    Knowledge("float32"),
    Knowledge("drop_spike"),
    Knowledge("partial", 0.999),
    Knowledge("partial", 0.99),
    Knowledge("partial", 0.9),
    Knowledge("partial", 0.5),
]

_parts: tuple[Connectome, FlySenses, FlyDecoder] | None = None


def parts() -> tuple[Connectome, FlySenses, FlyDecoder]:
    global _parts
    if _parts is None:
        enable_determinism()
        catalog = load_catalog()
        _parts = (
            load_connectome(),
            FlySenses.from_catalog(catalog),
            FlyDecoder.from_catalog(catalog),
        )
    return _parts


def run_one(
    job: tuple[str, Path, Knowledge | None, bool],
) -> tuple[str, Knowledge | None, bool, list[Pose], list[int]]:
    """Load the saved moment, optionally blur it, run ahead. `truth` marks the reference run."""
    moment, path, knowledge, truth = job
    connectome, senses, decoder = parts()
    timeline = Timeline.load(path, connectome, DECISION_ARENA, senses, decoder)
    if knowledge is not None:
        blur(timeline.brain.state, knowledge)
    poses, spikes = timeline.run_recording(HORIZON_MS)
    keys = (spikes.steps * connectome.n_neurons + spikes.neurons).tolist()
    return moment, knowledge, truth, poses, keys


def events(poses: list[Pose]) -> list[str]:
    out, feeding = [], poses[0].feeding
    for p in poses:
        if p.jumped:
            out.append(f"jump {p.time_ms / 1000:.3f}")
        if p.feeding != feeding:
            out.append(f"{'feed' if p.feeding else 'stop'} {p.time_ms / 1000:.3f}")
            feeding = p.feeding
    return out


def first_spike_difference_ms(a: list[int], b: list[int], n: int, start_step: int) -> int | None:
    only = set(a) ^ set(b)
    return (min(k // n for k in only) - start_step) // 10 if only else None


def main() -> None:
    connectome, senses, decoder = parts()
    workdir = Path(tempfile.mkdtemp())
    jobs: list[tuple[str, Path, Knowledge | None, bool]] = []
    timeline = Timeline(connectome, DECISION_ARENA, senses, decoder, seed=0, start=DEFAULT_START)
    for moment, at_ms in MOMENTS_MS.items():
        timeline.run(at_ms - timeline.fly.time_ms)
        path = workdir / f"{moment}.pt"
        timeline.save(path)
        jobs.append((moment, path, None, True))
        jobs += [(moment, path, k, False) for k in KNOWLEDGE]

    with ProcessPoolExecutor(max_workers=2) as pool:  # memory rule (ADR-0029, ADR-0032)
        results = list(pool.map(run_one, jobs))

    truth = {m: (poses, keys) for m, _, is_truth, poses, keys in results if is_truth}
    rows = []
    for moment, knowledge, is_truth, poses, keys in results:
        if is_truth:
            continue
        true_poses, true_keys = truth[moment]
        distances = path_distance_mm(poses, true_poses)
        first_path = first_divergence_ms(distances, EPSILON_MM)
        start_step = MOMENTS_MS[moment] * 10
        rows.append(
            {
                "moment": moment,
                "ghost_knows": "everything (control)"
                if knowledge is None
                else knowledge.describe(),
                "first_spike_difference_ms": first_spike_difference_ms(
                    keys, true_keys, connectome.n_neurons, start_step
                ),
                "path_stays_right_ms": HORIZON_MS if first_path is None else first_path,
                "distance_at_3s_mm": round(distances[-1], 3),
                "ghost_events": "; ".join(events(poses)),
                "true_events": "; ".join(events(true_poses)),
            }
        )
    ASSETS.mkdir(parents=True, exist_ok=True)
    out = ASSETS / "horizon.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for moment in MOMENTS_MS:
        mine = [r for r in rows if r["moment"] == moment]
        print(f"== {moment} (truth: {mine[0]['true_events'] or 'no events'})")
        for r in mine:
            stays = r["path_stays_right_ms"]
            right = "all 3 s" if stays == HORIZON_MS else f"{stays} ms"
            print(
                f"   {r['ghost_knows']:28} first spike off {r['first_spike_difference_ms']!s:>5} ms"
                f" | path right for {right:>8} | end {r['distance_at_3s_mm']:7.3f} mm"
                f" | {r['ghost_events'] or '-'}"
            )


if __name__ == "__main__":
    main()
