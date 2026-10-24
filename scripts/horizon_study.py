"""Result 1: how long does a ghost stay right when it knows the brain imperfectly? (ADR-0035)

At three moments of a run on the decision dish (walking, on laced food, under the
faint shadow) the true fly is saved. Ghosts start from that save with imperfect
knowledge (perturb.py) and run 3 s ahead next to the truth. The perfect ghost is the
control. For each ghost: when the first spike differs, when the paths separate by
more than 0.1 mm, and what the fly does differently.

    uv run python scripts/horizon_study.py                 # first pass: seed 0, one draw
    uv run python scripts/horizon_study.py --seeds 0 1 2 --draws 3 --set v2 --tag v2

The second pass (ADR-0038) repeats every random error with several draws, on several
runs of the brain (seeds), so each case gives a distribution rather than one number.
"""

from __future__ import annotations

import argparse
import csv
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

from tramlines.brain.connectome import Connectome, load_connectome
from tramlines.brain.engine import enable_determinism
from tramlines.brain.neurons import load_catalog
from tramlines.timeline.divergence import first_divergence_ms, path_distance_mm
from tramlines.timeline.perturb import Knowledge, NoSpikeInTransit, blur
from tramlines.timeline.timeline import Pose, Timeline
from tramlines.world.arena import DECISION_ARENA
from tramlines.world.decoder import FlyDecoder
from tramlines.world.fly import DEFAULT_START
from tramlines.world.senses import FlySenses

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
MOMENTS_MS = {"walking": 500, "laced food": 1200, "shadow": 3350}
HORIZON_MS = 3000
EPSILON_MM = 0.1
# First pass (ADR-0037): one value per decade.
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
# Second pass (ADR-0038): finer around the edge the first pass found (0.01-0.1 mV, 99-99.9%).
KNOWLEDGE_V2: list[Knowledge | None] = [
    None,
    Knowledge("voltage", 1e-3),
    Knowledge("voltage", 1e-2),
    Knowledge("voltage", 3e-2),
    Knowledge("voltage", 1e-1),
    Knowledge("voltage", 1.0),
    Knowledge("float32"),
    Knowledge("drop_spike"),
    Knowledge("partial", 0.999),
    Knowledge("partial", 0.995),
    Knowledge("partial", 0.99),
]
SETS = {"v1": KNOWLEDGE, "v2": KNOWLEDGE_V2}
RANDOM_KINDS = {"voltage", "drop_spike", "partial"}  # the others are the same on every draw
Job = tuple[int, str, Path, Knowledge | None, bool]

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


def run_one(job: Job) -> tuple[int, str, Knowledge | None, bool, list[Pose], list[int]]:
    """Load the saved moment, optionally blur it, run ahead. `truth` marks the reference run."""
    seed, moment, path, knowledge, truth = job
    connectome, senses, decoder = parts()
    timeline = Timeline.load(path, connectome, DECISION_ARENA, senses, decoder)
    if knowledge is not None:
        try:
            blur(timeline.brain.state, knowledge)
        except NoSpikeInTransit:
            return seed, moment, knowledge, truth, [], []  # reported as "nothing to miss"
    poses, spikes = timeline.run_recording(HORIZON_MS)
    keys = (spikes.steps * connectome.n_neurons + spikes.neurons).tolist()
    return seed, moment, knowledge, truth, poses, keys


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


def draws_of(knowledge: Knowledge | None, draws: int) -> list[Knowledge | None]:
    if knowledge is None or knowledge.kind not in RANDOM_KINDS:
        return [knowledge]
    return [replace(knowledge, seed=d) for d in range(draws)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, nargs="+", default=[0])
    parser.add_argument("--draws", type=int, default=1, help="random draws per random error")
    parser.add_argument("--set", choices=sorted(SETS), default="v1")
    parser.add_argument("--tag", default="", help="output horizon_<tag>.csv")
    parser.add_argument("--workers", type=int, default=2)  # memory rule (ADR-0029, ADR-0032)
    args = parser.parse_args()

    connectome, senses, decoder = parts()
    workdir = Path(tempfile.mkdtemp())
    jobs: list[Job] = []
    where: dict[tuple[int, str], str] = {}
    for seed in args.seeds:
        timeline = Timeline(
            connectome, DECISION_ARENA, senses, decoder, seed=seed, start=DEFAULT_START
        )
        for moment, at_ms in MOMENTS_MS.items():
            timeline.run(at_ms - timeline.fly.time_ms)
            fly = timeline.fly
            where[seed, moment] = f"({fly.x_mm:.1f}, {fly.y_mm:.1f}) feeding={fly.feeding}"
            path = workdir / f"{seed}-{moment}.pt"
            timeline.save(path)
            jobs.append((seed, moment, path, None, True))
            for k in SETS[args.set]:
                jobs += [(seed, moment, path, d, False) for d in draws_of(k, args.draws)]
    print(f"{len(jobs)} runs of {HORIZON_MS} ms on {args.workers} workers", flush=True)

    results = []
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for done, result in enumerate(pool.map(run_one, jobs), start=1):
            results.append(result)
            elapsed = time.monotonic() - started
            left = elapsed / done * (len(jobs) - done)
            print(f"  {done}/{len(jobs)} done, {elapsed / 60:.1f} min, ~{left / 60:.0f} min left",
                  flush=True)  # fmt: skip

    truth = {(s, m): (poses, keys) for s, m, _, is_truth, poses, keys in results if is_truth}
    rows, skipped = [], []
    for seed, moment, knowledge, is_truth, poses, keys in results:
        if is_truth:
            continue
        true_poses, true_keys = truth[seed, moment]
        row: dict[str, object] = {"moment": moment}
        if args.tag:
            row |= {
                "seed": seed,
                "draw": "-" if knowledge is None or knowledge.kind not in RANDOM_KINDS
                else knowledge.seed,
                "fly_at_moment": where[seed, moment],
            }  # fmt: skip
        described = "everything (control)" if knowledge is None else knowledge.describe()
        if not poses:  # nothing in transit to miss: no ghost was made (ADR-0038)
            skipped.append(f"{moment}, seed {seed}: {described}: none in transit")
            continue
        distances = path_distance_mm(poses, true_poses)
        first_path = first_divergence_ms(distances, EPSILON_MM)
        start_step = MOMENTS_MS[moment] * 10
        row |= {
            "ghost_knows": described,
            "first_spike_difference_ms": first_spike_difference_ms(
                keys, true_keys, connectome.n_neurons, start_step
            ),
            "path_stays_right_ms": HORIZON_MS if first_path is None else first_path,
            "distance_at_3s_mm": round(distances[-1], 3),
            "ghost_events": "; ".join(events(poses)),
            "true_events": "; ".join(events(true_poses)),
        }
        rows.append(row)
    ASSETS.mkdir(parents=True, exist_ok=True)
    out = ASSETS / (f"horizon_{args.tag}.csv" if args.tag else "horizon.csv")
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {out.name}")
    for line in skipped:
        print(f"skipped ({line})")
    summarize(rows)


def summarize(rows: list[dict[str, object]]) -> None:
    """Per moment and kind of knowledge: how many ghosts stayed right, and the spread."""
    for moment in MOMENTS_MS:
        print(f"== {moment}")
        mine = [r for r in rows if r["moment"] == moment]
        for label in dict.fromkeys(str(r["ghost_knows"]) for r in mine):
            stays = sorted(int(str(r["path_stays_right_ms"])) for r in mine
                           if r["ghost_knows"] == label)  # fmt: skip
            right = sum(v == HORIZON_MS for v in stays)
            median = stays[len(stays) // 2]
            print(
                f"   {label:28} right all 3 s: {right:>2}/{len(stays):<2}"
                f" | median {median:>5} ms | range {stays[0]}-{stays[-1]} ms"
            )


if __name__ == "__main__":
    main()
