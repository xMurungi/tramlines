"""Result 3: the perturbation atlas, as pre-registered (docs/science/atlas-plan.md).

24 cells (seeds 0-2 x 8 moments on the decision dish). In each, three groups of neurons
get one extra spike: 2,000 drawn from all neurons, 300 from the awake ones, and every
driven input neuron. Each extra spike is screened for 30 ms; samples of cascades and
non-cascades are followed for 3 s; tipping points are rerun under three decoders.

    uv run python scripts/atlas_study.py                    # the study, 2 workers
    uv run python scripts/atlas_study.py --pipeline-test    # one small cell, not analysed
"""

from __future__ import annotations

import argparse
import csv
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import torch
from horizon_study import parts

from tramlines.brain.engine import SpikeRecord
from tramlines.timeline.atlas import Outcome, awake_neurons, outcome, screen, spike_keys
from tramlines.timeline.timeline import BRAIN_STEPS_PER_WORLD_STEP, Timeline
from tramlines.world.arena import DECISION_ARENA
from tramlines.world.decoder import FlyDecoder
from tramlines.world.fly import DEFAULT_START

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
SEEDS = (0, 1, 2)
MOMENTS_MS = (250, 750, 1_250, 1_750, 2_250, 2_750, 3_250, 3_750)
GROUP_SIZES = {"random": 2_000, "awake": 300}  # "inputs": all of them
SCREEN_MS, HORIZON_MS = 30, 3_000
FOLLOW_CASCADES, FOLLOW_QUIET = 20, 10
DECODER_TIPPING, DECODER_CONTROLS = 10, 3
LONG_WINDOW_MS = 100
# (cell seed, moment, saved state, readout counts for the last LONG_WINDOW_MS ms, pipeline?)
Job = tuple[int, int, Path, torch.Tensor, bool]


def draw(pool: list[int], k: int, seed: int) -> list[int]:
    """Up to k of `pool`, uniformly, with their own generator (plan: Design)."""
    if len(pool) <= k:
        return sorted(pool)
    order = torch.randperm(len(pool), generator=torch.Generator().manual_seed(seed))[:k]
    return sorted(pool[int(i)] for i in order)


def readout_counts(
    record: SpikeRecord, readouts: torch.Tensor, start_ms: int, ms: int
) -> torch.Tensor:
    """Spikes of each readout neuron in each millisecond [start_ms, start_ms + ms)."""
    slot_of = {int(n): i for i, n in enumerate(readouts.tolist())}
    counts = torch.zeros((ms, len(slot_of)), dtype=torch.int64)
    for step, neuron in zip(record.steps.tolist(), record.neurons.tolist(), strict=True):
        if neuron in slot_of:
            counts[step // BRAIN_STEPS_PER_WORLD_STEP - start_ms, slot_of[neuron]] += 1
    return counts


def window_from(counts: torch.Tensor, now_ms: int, window_ms: int) -> torch.Tensor:
    """The decoder's window as Timeline keeps it: ms t's counts live in row t % window_ms."""
    window = torch.zeros((window_ms, counts.shape[1]), dtype=torch.int64)
    for back in range(1, window_ms + 1):
        t = now_ms - back
        window[t % window_ms] = counts[counts.shape[0] - back]
    return window


def outcome_row(o: Outcome) -> dict[str, object]:
    return {"made": o.made, "why_not": o.why_not, "choice_differs": o.choice_differs,
            "behaviour_differs": o.behaviour_differs,
            "path_wrong_from_ms": "" if o.path_wrong_from_ms is None else o.path_wrong_from_ms,
            "events": "; ".join(f"{e.kind} {e.time_ms}" for e in o.events)}  # fmt: skip


def run_cell(job: Job) -> dict[str, list[dict[str, object]]]:
    seed, at_ms, path, recent, pipeline = job
    connectome, senses, decoder = parts()
    base = Timeline.load(path, connectome, DECISION_ARENA, senses, decoder)
    n = connectome.n_neurons
    cell = {"seed": seed, "moment_ms": at_ms}
    sizes = {k: (5 if pipeline else v) for k, v in GROUP_SIZES.items()}
    groups = {
        "random": draw(list(range(n)), sizes["random"], seed * 10_000 + at_ms),
        "awake": draw(awake_neurons(base).tolist(), sizes["awake"], seed * 10_000 + at_ms + 1),
        "inputs": sorted(senses.input_neurons.tolist())[: 5 if pipeline else None],
    }
    truth_keys = spike_keys(base.fork().run_recording(SCREEN_MS)[1], n)
    truth_poses = base.fork().run(HORIZON_MS)

    screens: list[dict[str, object]] = []
    for group, neurons in groups.items():
        for neuron in neurons:
            s = screen(base, neuron, truth_keys, SCREEN_MS)
            screens.append(cell | {"group": group, "neuron": neuron, "made": s.made,
                                   "why_not": s.why_not, "spike_differences": s.spike_differences,
                                   "first_difference_ms": "" if s.first_difference_ms is None
                                   else s.first_difference_ms})  # fmt: skip

    follows: list[dict[str, object]] = []
    for group in groups:
        made = [r for r in screens if r["group"] == group and r["made"]]
        cascades = [int(str(r["neuron"])) for r in made if int(str(r["spike_differences"])) > 0]
        quiet = [int(str(r["neuron"])) for r in made if int(str(r["spike_differences"])) == 0]
        chosen = [(nn, True) for nn in draw(cascades, FOLLOW_CASCADES, seed * 10_000 + at_ms + 2)]
        chosen += [(nn, False) for nn in draw(quiet, FOLLOW_QUIET, seed * 10_000 + at_ms + 3)]
        for neuron, cascade in chosen:
            o = outcome(base, neuron, truth_poses, HORIZON_MS)
            follows.append(cell | {"group": group, "neuron": neuron, "cascade": cascade}
                           | outcome_row(o))  # fmt: skip

    tipping = sorted({int(str(r["neuron"])) for r in follows if r["choice_differs"] is True})
    steady = sorted({int(str(r["neuron"])) for r in follows
                     if r["cascade"] and r["choice_differs"] is False} - set(tipping))  # fmt: skip
    picked = [(nn, True) for nn in draw(tipping, DECODER_TIPPING, seed * 10_000 + at_ms + 4)]
    picked += [(nn, False) for nn in draw(steady, DECODER_CONTROLS, seed * 10_000 + at_ms + 5)]
    variants: dict[str, FlyDecoder] = {
        "window 100 ms": replace(decoder, window_ms=LONG_WINDOW_MS),
        "thresholds x1.2": decoder.scaled(1.2),
        "thresholds x0.8": decoder.scaled(0.8),
    }
    reruns: list[dict[str, object]] = []
    for name, variant in variants.items():
        if not picked:
            break
        moved = Timeline.load(path, connectome, DECISION_ARENA, senses, variant)
        if variant.window_ms != decoder.window_ms:
            moved.window = window_from(recent, at_ms, variant.window_ms)
        variant_truth = moved.fork().run(HORIZON_MS)
        for neuron, was_tipping in picked:
            o = outcome(moved, neuron, variant_truth, HORIZON_MS)
            reruns.append(cell | {"variant": name, "neuron": neuron,
                                  "tipping_by_default": was_tipping} | outcome_row(o))  # fmt: skip
    return {"screen": screens, "outcomes": follows, "decoder": reruns}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workers", type=int, default=2)  # memory rule (ADR-0029, ADR-0032)
    parser.add_argument("--pipeline-test", action="store_true")
    args = parser.parse_args()
    connectome, senses, decoder = parts()
    readouts = decoder.readout_neurons.to(torch.int64)
    workdir = Path(tempfile.mkdtemp())
    jobs: list[Job] = []
    for seed in SEEDS[:1] if args.pipeline_test else SEEDS:
        timeline = Timeline(connectome, DECISION_ARENA, senses, decoder, seed=seed,
                            start=DEFAULT_START)  # fmt: skip
        history = torch.zeros((0, len(readouts)), dtype=torch.int64)
        for at_ms in MOMENTS_MS[:1] if args.pipeline_test else MOMENTS_MS:
            start = timeline.fly.time_ms
            _, record = timeline.run_recording(at_ms - start)
            history = torch.cat([history, readout_counts(record, readouts, start, at_ms - start)])
            # The check in the plan: rebuilding the default window reproduces the saved one.
            if not torch.equal(window_from(history, at_ms, decoder.window_ms), timeline.window):
                raise RuntimeError(f"window rebuild mismatch at seed {seed}, {at_ms} ms")
            path = workdir / f"{seed}-{at_ms}.pt"
            timeline.save(path)
            jobs.append((seed, at_ms, path, history[-LONG_WINDOW_MS:].clone(), args.pipeline_test))
    print(f"{len(jobs)} cells on {args.workers} workers; window rebuild checked", flush=True)
    tables: dict[str, list[dict[str, object]]] = {"screen": [], "outcomes": [], "decoder": []}
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for done, result in enumerate(pool.map(run_cell, jobs), start=1):
            for key, rows in result.items():
                tables[key] += rows
            elapsed = time.monotonic() - started
            left = elapsed / done * (len(jobs) - done)
            print(f"  {done}/{len(jobs)} cells, {elapsed / 60:.1f} min, ~{left / 60:.0f} min left",
                  flush=True)  # fmt: skip
    folder = Path(tempfile.mkdtemp()) if args.pipeline_test else ASSETS
    for key, rows in tables.items():
        out = folder / f"atlas_{key}.csv"
        if rows:
            with out.open("w", newline="") as f:
                fields = list(dict.fromkeys(k for r in rows for k in r))
                writer = csv.DictWriter(f, fieldnames=fields, restval="")
                writer.writeheader()
                writer.writerows(rows)
        print(f"wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
