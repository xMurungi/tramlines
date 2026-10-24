"""Result 3 pilot: how often does one extra spike cascade, and what does each test cost?

Exploratory, to size the pre-registered study (the Result 4 pattern, ADR-0040). Seed 0 on
the decision dish, four moments. At each, three groups of neurons get one extra spike:
every input neuron; a sample of the neurons awake right then; a uniform sample of all.
Each is screened for 30 ms (any other spike changed?). Up to MAX_FOLLOW cascading spikes
per group, and SCREENED_OUT_FOLLOW that did not cascade, are followed for 3 s of behaviour.

    uv run python scripts/atlas_pilot.py
"""

from __future__ import annotations

import csv
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import torch
from horizon_study import parts

from tramlines.timeline.atlas import awake_neurons, outcome, screen, spike_keys
from tramlines.timeline.timeline import Timeline
from tramlines.world.arena import DECISION_ARENA
from tramlines.world.fly import DEFAULT_START

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
SEED = 0
MOMENTS_MS = (500, 1200, 2000, 3350)
AWAKE_SAMPLE, RANDOM_SAMPLE = 200, 300
SCREEN_MS, HORIZON_MS = 30, 3_000
MAX_FOLLOW, SCREENED_OUT_FOLLOW = 15, 10
Job = tuple[int, Path]


def blank(value: int | None) -> int | str:
    return "" if value is None else value


def sample(pool: torch.Tensor, k: int, seed: int) -> list[int]:
    chooser = torch.Generator().manual_seed(seed)
    order = torch.randperm(len(pool), generator=chooser)[:k]
    return sorted(pool[order].tolist())


def run_moment(job: Job) -> list[dict[str, object]]:
    at_ms, path = job
    connectome, senses, decoder = parts()
    base = Timeline.load(path, connectome, DECISION_ARENA, senses, decoder)
    n = connectome.n_neurons
    groups = {
        "inputs": sorted(senses.input_neurons.tolist()),
        "awake": sample(awake_neurons(base), AWAKE_SAMPLE, seed=at_ms),
        "random": sample(torch.arange(n), RANDOM_SAMPLE, seed=at_ms + 1),
    }
    truth = spike_keys(base.fork().run_recording(SCREEN_MS)[1], n)
    truth_poses = base.fork().run(HORIZON_MS)
    rows: list[dict[str, object]] = []
    for group, neurons in groups.items():
        followed = screened_out_followed = 0
        for neuron in neurons:
            t0 = time.perf_counter()
            s = screen(base, neuron, truth, SCREEN_MS)
            row: dict[str, object] = {
                "moment_ms": at_ms, "group": group, "neuron": neuron, "made": s.made,
                "why_not": s.why_not, "spike_differences": s.spike_differences,
                "first_difference_ms": blank(s.first_difference_ms),
                "screen_s": round(time.perf_counter() - t0, 3),
            }  # fmt: skip
            cascade = s.made and s.spike_differences > 0
            follow = (cascade and followed < MAX_FOLLOW) or (
                s.made and not cascade and screened_out_followed < SCREENED_OUT_FOLLOW
            )
            if follow:
                followed += cascade
                screened_out_followed += not cascade
                t0 = time.perf_counter()
                o = outcome(base, neuron, truth_poses, HORIZON_MS)
                row |= {
                    "followed": True,
                    "path_wrong_from_ms": ""
                    if o.path_wrong_from_ms is None
                    else o.path_wrong_from_ms,
                    "behaviour_differs": o.behaviour_differs,
                    "outcome_s": round(time.perf_counter() - t0, 1),
                }
            rows.append(row)
    return rows


def main() -> None:
    connectome, senses, decoder = parts()
    workdir = Path(tempfile.mkdtemp())
    timeline = Timeline(connectome, DECISION_ARENA, senses, decoder, seed=SEED, start=DEFAULT_START)
    jobs: list[Job] = []
    for at_ms in MOMENTS_MS:
        timeline.run(at_ms - timeline.fly.time_ms)
        path = workdir / f"{at_ms}.pt"
        timeline.save(path)
        jobs.append((at_ms, path))
    rows: list[dict[str, object]] = []
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=2) as pool:  # memory rule (ADR-0029, ADR-0032)
        for done, result in enumerate(pool.map(run_moment, jobs), start=1):
            rows += result
            print(f"  {done}/{len(jobs)} moments done, {(time.monotonic() - started) / 60:.1f} min",
                  flush=True)  # fmt: skip
    fields = list(dict.fromkeys(k for r in rows for k in r))
    out = ASSETS / "atlas_pilot.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, restval="")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {out.name}")


if __name__ == "__main__":
    main()
