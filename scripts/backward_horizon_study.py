"""Result 4: the backward horizon. How long can a demon still recover the past? (ADR-0040)

Implements the pre-registered plan, docs/science/backward-horizon-plan.md: for each
seed and moment on the decision dish, pairs of timelines (truth, and one altered by a
small difference in the past) run 3 s side by side. Every 10 ms the brains' states are
compared (`divergence.brain_difference`), and the bodies at the end. For each precision
ε, B(ε) is when the pasts became indistinguishable for good (censored if never).

    uv run python scripts/backward_horizon_study.py           # the full study, 2 workers
    uv run python scripts/backward_horizon_study.py --pipeline-test
    uv run python scripts/backward_horizon_study.py --replace 2 walking "extra spike"

`--replace` reruns one (seed, moment, kind) group and swaps its rows in the CSV: used
once, after a fix to `inject_spike` (a deviation listed in ADR-0041).
"""

from __future__ import annotations

import argparse
import csv
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import torch
from horizon_study import MOMENTS_MS, parts

from tramlines.brain.engine import Brain
from tramlines.timeline.divergence import brain_difference
from tramlines.timeline.perturb import Knowledge, NoSpikeInTransit, blur
from tramlines.timeline.timeline import Timeline
from tramlines.world.arena import DECISION_ARENA
from tramlines.world.fly import DEFAULT_START

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
SEEDS = (0, 1, 2)
HORIZON_MS = 3_000
SAMPLE_MS = 10
TRACE_MS = 100
EPSILONS_MV = (1e-13, 1e-11, 1e-9, 1e-6, 1e-3)
VOLTAGE_SIGMAS_MV = (1e-9, 1e-6, 1e-3, 1e-1)
DRAWS = (0, 1, 2)
# (kind, amount, draw); kind is "voltage", "missed spike" or "extra spike"
Difference = tuple[str, float, int]
Job = tuple[int, str, Path, Difference]


def differences() -> list[Difference]:
    out: list[Difference] = [("voltage", s, d) for s in VOLTAGE_SIGMAS_MV for d in DRAWS]
    out += [("missed spike", 0.0, d) for d in DRAWS]
    out += [("extra spike", 0.0, d) for d in DRAWS]
    return out


def can_fire(brain: Brain, neuron: int) -> bool:
    """The engine's own tests in `inject_spike`: did not fire at the step just ended, and
    not refractory (deviation from the first run, ADR-0041: the first check was missing)."""
    s = brain.state
    just_now, last = s.step - 1, int(s.last_spike_step[neuron])
    return last != just_now and just_now - last >= int(brain.refractory_steps[neuron])


def make_difference(timeline: Timeline, difference: Difference) -> str:
    """Apply it; return a description, or raise NoSpikeInTransit / LookupError if impossible."""
    kind, amount, draw = difference
    state = timeline.brain.state
    if kind == "voltage":
        blur(state, Knowledge("voltage", amount, seed=draw))
        return f"voltage noise {amount:g} mV"
    if kind == "missed spike":
        blur(state, Knowledge("drop_spike", seed=draw))
        return "one spike in transit missed"
    # The draw-th walking-drive neuron, by index, that can fire now (ADR-0031).
    walk = sorted(timeline.senses.walk_drive.tolist())  # type: ignore[attr-defined]
    able = [n for n in walk if can_fire(timeline.brain, n)]
    if draw >= len(able):
        raise LookupError("not enough walking-drive neurons able to fire")
    timeline.brain.inject_spike(able[draw])
    return f"one extra spike (neuron {able[draw]})"


def run_pair(job: Job) -> dict[str, object]:
    seed, moment, path, difference = job
    connectome, senses, decoder = parts()
    truth = Timeline.load(path, connectome, DECISION_ARENA, senses, decoder)
    altered = Timeline.load(path, connectome, DECISION_ARENA, senses, decoder)
    kind, amount, draw = difference
    row: dict[str, object] = {
        "seed": seed,
        "moment": moment,
        "kind": kind,
        "amount_mV": amount if kind == "voltage" else "",
        "draw": draw,
    }
    try:
        row["difference"] = make_difference(altered, difference)
    except (NoSpikeInTransit, LookupError) as reason:
        return row | {"made": False, "why_not": str(reason)}
    since_brain: dict[float, int | None] = dict.fromkeys(EPSILONS_MV)
    since_full: dict[float, int | None] = dict.fromkeys(EPSILONS_MV)
    trace: list[str] = []
    for t in range(SAMPLE_MS, HORIZON_MS + 1, SAMPLE_MS):
        truth.run(SAMPLE_MS)
        altered.run(SAMPLE_MS)
        d = brain_difference(truth.brain, altered.brain)
        body_same = truth.fly.fingerprint() == altered.fly.fingerprint() and torch.equal(
            truth.window, altered.window
        )
        for eps in EPSILONS_MV:
            # Indistinguishable for good: the streak must last to the end of the run.
            below = d.below(eps)
            since_brain[eps] = (since_brain[eps] or t) if below else None
            since_full[eps] = (since_full[eps] or t) if below and body_same else None
        if t % TRACE_MS == 0:
            trace.append(f"{d.max_dv_mV:.2e}")
    fly_t, fly_a = truth.fly, altered.fly
    row |= {"made": True, "why_not": ""}
    for eps in EPSILONS_MV:
        row[f"B_brain_{eps:g}"] = since_brain[eps] if since_brain[eps] is not None else ""
    for eps in EPSILONS_MV:
        row[f"B_full_{eps:g}"] = since_full[eps] if since_full[eps] is not None else ""
    row |= {
        "body_differs": fly_t.fingerprint() != fly_a.fingerprint(),
        "body_apart_mm": round(
            ((fly_t.x_mm - fly_a.x_mm) ** 2 + (fly_t.y_mm - fly_a.y_mm) ** 2) ** 0.5, 4
        ),
        "dv_trace_per_100ms": " ".join(trace),
    }
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workers", type=int, default=2)  # memory rule (ADR-0029, ADR-0032)
    parser.add_argument("--pipeline-test", action="store_true",
                        help="one pair, not analysed (plan: pipeline test)")  # fmt: skip
    parser.add_argument("--replace", nargs=3, metavar=("SEED", "MOMENT", "KIND"),
                        help="rerun one group and replace its rows in the CSV")  # fmt: skip
    args = parser.parse_args()
    connectome, senses, decoder = parts()
    workdir = Path(tempfile.mkdtemp())
    jobs: list[Job] = []
    seeds = (int(args.replace[0]),) if args.replace else SEEDS[:1] if args.pipeline_test else SEEDS
    for seed in seeds:
        timeline = Timeline(connectome, DECISION_ARENA, senses, decoder, seed=seed,
                            start=DEFAULT_START)  # fmt: skip
        for moment, at_ms in MOMENTS_MS.items():
            timeline.run(at_ms - timeline.fly.time_ms)
            path = workdir / f"{seed}-{moment}.pt"
            timeline.save(path)
            jobs += [(seed, moment, path, d) for d in differences()]
    if args.pipeline_test:
        jobs = [j for j in jobs if j[1] == "shadow" and j[3] == ("extra spike", 0.0, 0)]
    if args.replace:
        jobs = [j for j in jobs if j[1] == args.replace[1] and j[3][0] == args.replace[2]]
    print(f"{len(jobs)} pairs of {HORIZON_MS} ms on {args.workers} workers", flush=True)
    rows: list[dict[str, object]] = []
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for done, row in enumerate(pool.map(run_pair, jobs), start=1):
            rows.append(row)
            elapsed = time.monotonic() - started
            left = elapsed / done * (len(jobs) - done)
            print(f"  {done}/{len(jobs)} done, {elapsed / 60:.1f} min, ~{left / 60:.0f} min left",
                  flush=True)  # fmt: skip
    if args.replace:
        old = list(csv.DictReader((ASSETS / "backward_horizon.csv").open()))
        group = (args.replace[0], args.replace[1], args.replace[2])
        kept = [r for r in old if (r["seed"], r["moment"], r["kind"]) != group]
        print(f"replacing {len(old) - len(kept)} rows")
        rows = [*kept, *rows]
    fields = list(dict.fromkeys(k for r in rows for k in r))
    name = "backward_horizon_pipeline_test.csv" if args.pipeline_test else "backward_horizon.csv"
    out = (Path(tempfile.gettempdir()) if args.pipeline_test else ASSETS) / name
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, restval="")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
