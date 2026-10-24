"""Result 2: what does the real wiring contribute to behaviour? (ADR-0035, ADR-0039)

The same senses, decoder and arena drive two kinds of brain: the real v783 connectome
and degree-preserving shuffles of it (null brains, tramlines/brain/null.py). Each
brain is tested two ways:

- **arena:** 10 s in the default dish from the usual start (food, bitter, a shadow
  at 6 s), as in the Phase 3 gate run;
- **probes:** the fly held in place for 1 s in each situation (walking ground, food,
  bitter, food laced with bitter, a looming shadow), so every pathway is tested even
  if a brain never walks to it. The body's commands are computed but not obeyed.

    uv run python scripts/null_brain_study.py                       # real + 5 nulls, 3 seeds
    uv run python scripts/null_brain_study.py --nulls 0 1 --seeds 0
    uv run python scripts/null_brain_study.py --fractions 0.01 0.05 0.1 0.25 0.5 \
        --nulls 0 1 2 --seeds 0 --no-real --tag sweep    # rewire only part of the wiring
"""

from __future__ import annotations

import argparse
import csv
import itertools
import math
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import torch

from tramlines.brain.connectome import Connectome, load_connectome
from tramlines.brain.engine import enable_determinism
from tramlines.brain.neurons import load_catalog
from tramlines.brain.null import shuffled
from tramlines.brain.params import PARAMS
from tramlines.timeline.timeline import Pose, Timeline
from tramlines.world.arena import DEFAULT_ARENA, Arena, Loom, Patch
from tramlines.world.decoder import FlyDecoder
from tramlines.world.fly import DEFAULT_START, FlyState
from tramlines.world.senses import (
    BITTER_HZ,
    LOOM_MAX_HZ,
    SUGAR_HZ,
    WALK_DRIVE_HZ,
    FlySenses,
)

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
ARENA_MS = 10_000
PROBE_MS = 1_000
LOOM_START_MS = 6_000  # DEFAULT_ARENA's shadow
HERE = FlyState(x_mm=0.0, y_mm=0.0, heading_rad=0.0)
# Each probe is a dish around the clamped fly. The shadow comes from its left.
PROBES: dict[str, Arena] = {
    "walking ground": Arena(),
    "food": Arena(patches=(Patch(0.0, 0.0, 5.0, "food"),)),
    "bitter": Arena(patches=(Patch(0.0, 0.0, 5.0, "bitter"),)),
    "laced food": Arena(patches=(Patch(0.0, 0.0, 5.0, "food"), Patch(0.0, 0.0, 5.0, "bitter"))),
    "shadow": Arena(looms=(Loom(start_ms=100, duration_ms=500, direction_rad=math.pi / 2),)),
}
# Readout groups, by position in FlyDecoder's fixed order.
GROUPS = {"P9": [0, 1, 2, 3], "DNa02": [4, 5], "MDN": [6, 7, 8, 9], "GF": [10, 11], "MN9": [12, 13]}
Job = tuple[str, int]  # (brain name, brain seed); brain names: see `brain_named`

_parts: tuple[Connectome, FlySenses, FlyDecoder] | None = None
_brains: dict[str, Connectome] = {}


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


def brain_named(name: str) -> Connectome:
    """ "real", "<seed>" (a full null brain) or "<seed>@<fraction>" (a partial one)."""
    real = parts()[0]
    if name not in _brains:
        if name == "real":
            _brains[name] = real
        else:
            seed, _, fraction = name.partition("@")
            _brains[name] = shuffled(real, int(seed), float(fraction or 1.0))
    return _brains[name]


def label(name: str) -> dict[str, object]:
    if name == "real":
        return {"brain": "real", "rewired": 0.0}
    seed, _, fraction = name.partition("@")
    return {"brain": f"null {seed}", "rewired": float(fraction or 1.0)}


def readout_rates_hz(
    spikes: list[tuple[int, torch.Tensor]], decoder: FlyDecoder, ms: int
) -> dict[str, float]:
    fired = torch.cat([f for _, f in spikes]) if spikes else torch.zeros(0, dtype=torch.int64)
    readouts = decoder.readout_neurons.to(torch.int64)
    counts = (
        (fired.unsqueeze(1) == readouts.unsqueeze(0)).sum(0).tolist()
        if len(fired)
        else [0] * len(readouts)
    )
    return {g: sum(counts[i] for i in idx) / len(idx) * 1000 / ms for g, idx in GROUPS.items()}


def activity(spikes: list[tuple[int, torch.Tensor]], n: int, ms: int) -> dict[str, float]:
    fired = torch.cat([f for _, f in spikes]) if spikes else torch.zeros(0, dtype=torch.int64)
    return {"neurons_active": len(torch.unique(fired)), "spikes_per_s": len(fired) * 1000 / ms}


def arena_run(connectome: Connectome, seed: int) -> dict[str, object]:
    _, senses, decoder = parts()
    timeline = Timeline(connectome, DEFAULT_ARENA, senses, decoder, seed=seed, start=DEFAULT_START)
    spikes: list[tuple[int, torch.Tensor]] = []
    poses: list[Pose] = [timeline.step(spikes) for _ in range(ARENA_MS)]
    path = sum(
        math.hypot(b.x_mm - a.x_mm, b.y_mm - a.y_mm)
        for a, b in itertools.pairwise(poses)
        if not b.jumped
    )
    on_food = [
        any(p.kind == "food" for p in DEFAULT_ARENA.patches_under(q.x_mm, q.y_mm)) for q in poses
    ]
    jumps = [p.time_ms for p in poses if p.jumped]
    return {
        "walked_mm": round(path, 1),
        "reached_food": any(on_food),
        "feeding_ms": sum(p.feeding for p in poses),
        "feeding_on_food_ms": sum(p.feeding and f for p, f in zip(poses, on_food, strict=True)),
        "jumps": len(jumps),
        "escaped_shadow": any(LOOM_START_MS <= t < LOOM_START_MS + 1000 for t in jumps),
        **activity(spikes, connectome.n_neurons, ARENA_MS),
    }


def probe(connectome: Connectome, seed: int, arena: Arena) -> dict[str, object]:
    """Hold the fly still in `arena` for PROBE_MS; record what it would do and its readouts."""
    _, senses, decoder = parts()
    timeline = Timeline(connectome, arena, senses, decoder, seed=seed, start=HERE)
    spikes: list[tuple[int, torch.Tensor]] = []
    feeding = jumps = 0
    for _ in range(PROBE_MS):
        pose = timeline.step(spikes)
        feeding += pose.feeding
        jumps += pose.jumped
        fly = timeline.fly  # clamp: the command is computed, then undone
        fly.x_mm, fly.y_mm, fly.heading_rad = HERE.x_mm, HERE.y_mm, HERE.heading_rad
    rates = readout_rates_hz(spikes, decoder, PROBE_MS)
    return {
        "feeding_ms": feeding,
        "jumps": jumps,
        **{f"{g}_hz": round(v, 1) for g, v in rates.items()},
        **activity(spikes, connectome.n_neurons, PROBE_MS),
    }


def convergence(name: str) -> list[dict[str, object]]:
    """Why a pathway works or not, without simulating: how strongly each sense converges.

    For each sensory port, sum the weights of its connections onto each receiving
    neuron. A port firing steadily at r Hz raises a receiver's mean voltage by
    r x tau_syn x (summed weight): exact for this linear model below threshold
    (the voltage response to one kick integrates to weight x tau_syn). The receiver
    is driven to fire if that rise reaches the threshold, 7 mV above rest (ADR-0016).
    """
    connectome = brain_named(name)
    _, senses, _ = parts()
    threshold_mV = PARAMS.v_threshold_mV - PARAMS.v_rest_mV
    ports = {
        "sugar": (senses.sugar, SUGAR_HZ),
        "bitter": (senses.bitter, BITTER_HZ),
        "loom (left)": (senses.loom_left, LOOM_MAX_HZ),
        "walking drive": (senses.walk_drive, WALK_DRIVE_HZ),
    }
    rows: list[dict[str, object]] = []
    for port, (neurons, rate_hz) in ports.items():
        post, weight = connectome.outgoing(neurons.to(torch.int64))
        summed = torch.zeros(connectome.n_neurons, dtype=torch.float64)
        summed.index_add_(0, post.to(torch.int64), weight)
        rise_mV = summed * (rate_hz / 1000.0) * PARAMS.tau_synapse_ms
        rows.append(
            {
                **label(name),
                "port": port,
                "port_neurons": len(neurons),
                "rate_hz": rate_hz,
                "receivers": int((summed != 0).sum()),
                "strongest_receiver_rise_mV": round(float(rise_mV.max()), 1),
                "receivers_driven_over_threshold": int((rise_mV >= threshold_mV).sum()),
            }
        )
    return rows


def run_job(job: Job) -> list[dict[str, object]]:
    name, seed = job
    connectome = brain_named(name)
    who = label(name)
    rows: list[dict[str, object]] = [
        {**who, "seed": seed, "test": "arena 10 s", **arena_run(connectome, seed)}
    ]
    for test, arena in PROBES.items():
        rows.append({**who, "seed": seed, "test": test, **probe(connectome, seed, arena)})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--nulls", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--fractions", type=float, nargs="+", default=[1.0],
                        help="share of connections rewired (1 = the full null brain)")  # fmt: skip
    parser.add_argument("--no-real", action="store_true", help="skip the real brain")
    parser.add_argument("--workers", type=int, default=2)  # memory rule (ADR-0029, ADR-0032)
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    # Jobs grouped by brain, so each worker shuffles each null once.
    brains = [] if args.no_real else ["real"]
    brains += [str(n) if f >= 1.0 else f"{n}@{f:g}" for f in args.fractions for n in args.nulls]
    jobs: list[Job] = [(b, s) for b in brains for s in args.seeds]
    print(
        f"{len(jobs)} brains x seeds, each {ARENA_MS // 1000} s arena + {len(PROBES)} probes",
        flush=True,
    )
    rows: list[dict[str, object]] = []
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for done, result in enumerate(pool.map(run_job, jobs), start=1):
            rows += result
            elapsed = time.monotonic() - started
            left = elapsed / done * (len(jobs) - done)
            print(
                f"  {done}/{len(jobs)} done, {elapsed / 60:.1f} min, ~{left / 60:.0f} min left",
                flush=True,
            )
    fields = list(dict.fromkeys(k for r in rows for k in r))
    ASSETS.mkdir(parents=True, exist_ok=True)
    out = ASSETS / (f"null_brain_{args.tag}.csv" if args.tag else "null_brain.csv")
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, restval="")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {out.name}")
    wiring = [row for b in brains for row in convergence(b)]
    out = ASSETS / (
        f"null_brain_convergence_{args.tag}.csv" if args.tag else "null_brain_convergence.csv"
    )
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(wiring[0]))
        writer.writeheader()
        writer.writerows(wiring)
    for row in wiring:
        print(row)
    for row in rows:
        shown = {k: v for k, v in row.items() if k not in ("brain", "seed", "test")}
        print(f"{row['brain']:>7} s{row['seed']} {row['test']:>14}: {shown}")


if __name__ == "__main__":
    main()
