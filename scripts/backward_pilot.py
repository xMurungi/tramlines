"""Pilot for the backward horizon (proposal ADR-0040): does this brain erase its past?

Laplace's demon also knows the past. Two pasts that differ slightly lead, some time
later, either to two different present states (the past is still recoverable, in
principle) or to the same present state, bit for bit (no demon can tell which past
happened). This pilot takes the decision dish at Result 1's three moments, makes a
small difference in the past, runs both timelines side by side for 2 s and compares
them every 10 ms.

"Same state" means the same *functional* state: voltages, synaptic inputs, spikes in
transit, which neurons are refractory, and the random stream. The engine also keeps
each neuron's last spike time, but uses it only during the 2.2 ms refractory period,
so beyond that it is bookkeeping, not brain.

    uv run python scripts/backward_pilot.py
"""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path

import torch
from horizon_study import MOMENTS_MS, parts

from tramlines.timeline.perturb import Knowledge, NoSpikeInTransit, blur
from tramlines.timeline.timeline import Timeline
from tramlines.world.arena import DECISION_ARENA
from tramlines.world.fly import DEFAULT_START

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
RUN_MS = 2_000
SAMPLE_MS = 10
DIFFERENCES = ["voltage 1e-09 mV", "voltage 0.001 mV", "one in-flight spike missed",
               "one extra spike"]  # fmt: skip


def make_different(timeline: Timeline, difference: str) -> None:
    state = timeline.brain.state
    if difference.startswith("voltage"):
        blur(state, Knowledge("voltage", float(difference.split()[1])))
    elif difference == "one in-flight spike missed":
        blur(state, Knowledge("drop_spike"))
    else:  # an extra spike in a walking-drive neuron that can fire now (free will, ADR-0031)
        for neuron in timeline.senses.walk_drive.tolist():  # type: ignore[attr-defined]
            try:
                timeline.brain.inject_spike(int(neuron))
                return
            except ValueError:
                continue
        raise RuntimeError("no walking-drive neuron could fire")


def functional(timeline: Timeline) -> dict[str, torch.Tensor]:
    brain, s = timeline.brain, timeline.brain.state
    since = (s.step - 1) - s.last_spike_step
    refractory = since < brain.refractory_steps
    return {"v": s.v_mV, "g": s.g_mV, "in_flight": s.in_flight, "refractory": refractory,
            "rng": s.generator.get_state()}  # fmt: skip


def compare(a: Timeline, b: Timeline) -> dict[str, object]:
    fa, fb = functional(a), functional(b)
    dv = (fa["v"] - fb["v"]).abs()
    same_brain = all(torch.equal(fa[k], fb[k]) for k in fa)
    fly_a, fly_b = a.fly, b.fly
    return {
        "same_brain": same_brain,
        "neurons_v_differ": int((dv > 0).sum()),
        "max_dv_mV": float(dv.max()),
        "same_fly": fly_a.fingerprint() == fly_b.fingerprint(),
        "fly_apart_mm": round(
            ((fly_a.x_mm - fly_b.x_mm) ** 2 + (fly_a.y_mm - fly_b.y_mm) ** 2) ** 0.5, 3
        ),
    }


def main() -> None:
    connectome, senses, decoder = parts()
    workdir = Path(tempfile.mkdtemp())
    truth = Timeline(connectome, DECISION_ARENA, senses, decoder, seed=0, start=DEFAULT_START)
    rows: list[dict[str, object]] = []
    for moment, at_ms in MOMENTS_MS.items():
        truth.run(at_ms - truth.fly.time_ms)
        path = workdir / f"{moment}.pt"
        truth.save(path)
        for difference in DIFFERENCES:
            a = Timeline.load(path, connectome, DECISION_ARENA, senses, decoder)
            b = Timeline.load(path, connectome, DECISION_ARENA, senses, decoder)
            try:
                make_different(b, difference)
            except NoSpikeInTransit:
                print(f"{moment:>10} | {difference:26} | not made: no spike in transit", flush=True)
                continue
            erased_at, samples = None, []
            for t in range(SAMPLE_MS, RUN_MS + 1, SAMPLE_MS):
                a.run(SAMPLE_MS)
                b.run(SAMPLE_MS)
                c = compare(a, b)
                # The brains count as having erased the difference only if they stay identical.
                erased_at = (erased_at or t) if c["same_brain"] else None
                if t in (100, 500, 1000, RUN_MS):
                    samples.append({"moment": moment, "difference": difference, "after_ms": t, **c})
            rows += [{**r, "brain_identical_from_ms": erased_at} for r in samples]
            fly = "same" if c["same_fly"] else f"differs by {c['fly_apart_mm']} mm"
            erased = "never (in 2 s)" if erased_at is None else f"{erased_at} ms"
            print(f"{moment:>10} | {difference:26} | brain identical from {erased:>14} | "
                  f"fly {fly} | at 2 s: {c['neurons_v_differ']} voltages differ, "
                  f"max {c['max_dv_mV']:.2e} mV", flush=True)  # fmt: skip
    out = ASSETS / "backward_pilot.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in rows for k in r)),
                                restval="")  # fmt: skip
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {out.name}")


if __name__ == "__main__":
    main()
