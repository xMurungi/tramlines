"""Result 2 without our body: does a brain carry sense-specific signals at all? (ADR-0039)

The arena and probe tests judge a brain through our readouts and decoder, which were
chosen and calibrated on the real wiring, so a null brain is partly judged by a
yardstick made for the real one. This test ignores the readouts and decoder. Each
brain is held in four situations (walking ground, food, bitter, shadow) for 1 s, on
several seeds, and every neuron except the driven input neurons is examined:

- **responsive neurons:** fire at least THRESHOLD_HZ above walking ground on average,
  and above it in every seed; grouped by how many synapses they sit from that sense;
- **readable situation:** with one seed held out, the situation is guessed from the
  activity of neurons two or more synapses from any input (nearest centroid,
  correlation); chance is 1 in 4.

Predictions were written before this script existed: docs/science/null-brain-predictions.md.

    uv run python scripts/decoder_free_study.py
"""

from __future__ import annotations

import argparse
import csv
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import torch
from null_brain_study import HERE, PROBES, brain_named, label, parts

from tramlines.brain.connectome import Connectome
from tramlines.timeline.timeline import Timeline

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
SITUATIONS = ["walking ground", "food", "bitter", "shadow"]
SENSES = ["food", "bitter", "shadow"]  # each compared with walking ground
PROBE_MS = 1_000
THRESHOLDS_HZ = (1.0, 5.0, 10.0)  # 5 Hz is the main one; the others check sensitivity
MAIN_THRESHOLD_HZ = 5.0
DEEP_HOPS = 2  # "deep" neurons: at least this many synapses from every input
Job = tuple[str, int]


def spike_counts(job: Job) -> tuple[str, int, dict[str, torch.Tensor]]:
    """Spikes per neuron in each situation, the fly held still (as the probes do)."""
    name, seed = job
    connectome = brain_named(name)
    _, senses, decoder = parts()
    counts: dict[str, torch.Tensor] = {}
    for situation in SITUATIONS:
        timeline = Timeline(connectome, PROBES[situation], senses, decoder, seed=seed, start=HERE)
        spikes: list[tuple[int, torch.Tensor]] = []
        for _ in range(PROBE_MS):
            timeline.step(spikes)
            fly = timeline.fly
            fly.x_mm, fly.y_mm, fly.heading_rad = HERE.x_mm, HERE.y_mm, HERE.heading_rad
        fired = torch.cat([f for _, f in spikes]) if spikes else torch.zeros(0, dtype=torch.int64)
        counts[situation] = torch.bincount(fired.to(torch.int64), minlength=connectome.n_neurons)
    return name, seed, counts


def hops_from(connectome: Connectome, sources: torch.Tensor) -> torch.Tensor:
    """Synapses from `sources` to every neuron (0 = a source; -1 = unreachable)."""
    distance = torch.full((connectome.n_neurons,), -1, dtype=torch.int64)
    frontier = torch.unique(sources.to(torch.int64))
    distance[frontier] = 0
    hop = 0
    while len(frontier):
        hop += 1
        post, _ = connectome.outgoing(frontier)
        post = torch.unique(post.to(torch.int64))
        frontier = post[distance[post] < 0]
        distance[frontier] = hop
    return distance


def readable(counts: dict[int, dict[str, torch.Tensor]], neurons: torch.Tensor) -> tuple[int, int]:
    """Held-out-seed guesses of the situation from `neurons`' activity: (right, trials)."""
    right = trials = 0
    seeds = sorted(counts)
    for held in seeds:
        centroids = {
            s: torch.stack([counts[k][s][neurons] for k in seeds if k != held])
            .double()
            .log1p()
            .mean(0)
            for s in SITUATIONS
        }
        for truth in SITUATIONS:
            trial = counts[held][truth][neurons].double().log1p()
            guess = max(SITUATIONS, key=lambda s: _correlation(trial, centroids[s]))
            right += guess == truth
            trials += 1
    return right, trials


def _correlation(a: torch.Tensor, b: torch.Tensor) -> float:
    a, b = a - a.mean(), b - b.mean()
    norm = float(a.norm() * b.norm())
    return float((a * b).sum()) / norm if norm > 0 else -1.0  # silence matches nothing


def analyse(name: str, counts: dict[int, dict[str, torch.Tensor]]) -> list[dict[str, object]]:
    connectome = brain_named(name)
    _, senses, decoder = parts()
    inputs = senses.input_neurons.to(torch.int64)
    ports = {"food": senses.sugar, "bitter": senses.bitter,
             "shadow": torch.cat([senses.loom_left, senses.loom_right])}  # fmt: skip
    is_input = torch.zeros(connectome.n_neurons, dtype=torch.bool)
    is_input[inputs] = True
    seconds = PROBE_MS / 1000
    rows: list[dict[str, object]] = []
    for sense in SENSES:
        hops = hops_from(connectome, ports[sense])
        rate = torch.stack([counts[k][sense] for k in counts]).double() / seconds
        base = torch.stack([counts[k]["walking ground"] for k in counts]).double() / seconds
        always_above = (rate.min(0).values > base.max(0).values) & ~is_input
        row: dict[str, object] = {**label(name), "sense": sense}
        for threshold in THRESHOLDS_HZ:
            responsive = always_above & (rate.mean(0) - base.mean(0) >= threshold)
            tag = f"{threshold:g}hz"
            row[f"responsive_{tag}"] = int(responsive.sum())
            if threshold == MAIN_THRESHOLD_HZ:
                found = hops[responsive]
                for h in (1, 2, 3):
                    row[f"at_{h}_synapses"] = int((found == h).sum())
                row["at_4plus_synapses"] = int((found >= 4).sum())
                row["deepest"] = int(found.max()) if len(found) else 0
                readouts = decoder.readout_neurons.to(torch.int64)
                row["readouts_responsive"] = int(responsive[readouts].sum())
        rows.append(row)
    # The situation from deep neurons only: two or more synapses from every input.
    deep = torch.nonzero(hops_from(connectome, inputs) >= DEEP_HOPS).flatten()
    right, trials = readable(counts, deep)
    active_deep = sum(int((c[s][deep] > 0).sum()) for c in counts.values() for s in SITUATIONS)
    rows.append(
        {
            **label(name),
            "sense": "all four (readable?)",
            "read_right": right,
            "read_trials": trials,
            "deep_neurons": len(deep),
            "deep_active_mean": round(active_deep / (len(counts) * len(SITUATIONS)), 1),
        }
    )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--brains", nargs="+",
                        default=["real", "0", "1", "2", "3", "4", "0@0.1", "1@0.1", "2@0.1",
                                 "0@0.5", "1@0.5", "2@0.5", "0@0.9", "1@0.9", "2@0.9"])  # fmt: skip
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--workers", type=int, default=2)  # memory rule (ADR-0029, ADR-0032)
    args = parser.parse_args()
    jobs: list[Job] = [(b, s) for b in args.brains for s in args.seeds]
    print(f"{len(jobs)} runs: {len(SITUATIONS)} situations x {PROBE_MS} ms each", flush=True)
    collected: dict[str, dict[int, dict[str, torch.Tensor]]] = {b: {} for b in args.brains}
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for done, (name, seed, counts) in enumerate(pool.map(spike_counts, jobs), start=1):
            collected[name][seed] = counts
            elapsed = time.monotonic() - started
            left = elapsed / done * (len(jobs) - done)
            print(f"  {done}/{len(jobs)} done, {elapsed / 60:.1f} min, ~{left / 60:.0f} min left",
                  flush=True)  # fmt: skip
    rows = [row for b in args.brains for row in analyse(b, collected[b])]
    fields = list(dict.fromkeys(k for r in rows for k in r))
    out = ASSETS / "decoder_free.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, restval="")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {out.name}")
    for row in rows:
        print({k: v for k, v in row.items() if v != ""})


if __name__ == "__main__":
    main()
