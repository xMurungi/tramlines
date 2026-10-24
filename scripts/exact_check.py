"""Result 4's exact-arithmetic check: is the rounding floor the computer's, not the model's?

The backward-horizon pilot (ADR-0040) found that two brains whose voltages differed by
10⁻⁹ mV never become identical: the difference freezes near 10⁻¹² mV. The explanation
offered is float64 rounding. This check tests it (pre-registered hypothesis H5,
docs/science/backward-horizon-plan.md):

1. `generic_step` repeats the engine's step (tests/_reference_engine.py) for any kind
   of number. Run with Python floats from a saved state of the 400-neuron test
   network, it must match the engine bit for bit (this validates it).
2. Two pasts (voltage noise of 10⁻⁹ mV) then run 1 s in float64 and in 50-digit
   decimal arithmetic, with the same Poisson draws, and their difference is tracked.

    uv run python scripts/exact_check.py
"""

from __future__ import annotations

import csv
import sys
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
from _scenarios import run as run_schedule  # type: ignore[import-not-found]
from _scenarios import small

from tramlines.brain.engine import Brain, enable_determinism
from tramlines.brain.params import PARAMS
from tramlines.timeline.perturb import Knowledge, blur

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
DIGITS = 50
VALIDATE_STEPS = 2_000
RUN_STEPS = 10_000  # 1 s
SAMPLE_STEPS = 100  # every 10 ms
RATE_HZ = 150.0
SIGMA_MV = 1e-9


@dataclass
class Net:
    """The wiring and constants, in one kind of number."""

    row_start: list[int]
    post: list[int]
    weight: list[Any]
    inputs: list[int]
    refractory: list[int]
    v_rest: Any
    v_reset: Any
    v_th: Any
    decay_v: Any
    decay_g: Any
    g_to_v: Any
    kick: Any
    delay: int


@dataclass
class State:
    step: int
    v: list[Any]
    g: list[Any]
    last: list[int]
    in_flight: list[list[int]]  # per slot, the neurons whose spikes travel, ascending


def make_net(brain: Brain, num: Callable[[float], Any], exact: bool) -> Net:
    c, p = brain.connectome, brain.params
    decay_v: Any
    decay_g: Any
    g_to_v: Any
    kick: Any
    if exact:  # the model's constants computed afresh at 50 digits
        dt, tm, ts = Decimal("0.1"), Decimal(20), Decimal(5)
        decay_v, decay_g = (-dt / tm).exp(), (-dt / ts).exp()
        g_to_v = ts / (tm - ts) * (decay_v - decay_g)
        kick = Decimal("0.275") * 250
    else:
        decay_v, decay_g, g_to_v, kick = p.decay_v, p.decay_g, p.g_to_v, p.poisson_kick_mV
    return Net(
        row_start=c.row_start.tolist(),
        post=c.post.tolist(),
        weight=[num(w) for w in c.weight_mV.tolist()],
        inputs=brain.input_neurons.tolist(),
        refractory=brain.refractory_steps.tolist(),
        v_rest=num(p.v_rest_mV),
        v_reset=num(p.v_reset_mV),
        v_th=num(p.v_threshold_mV),
        decay_v=decay_v,
        decay_g=decay_g,
        g_to_v=g_to_v,
        kick=kick,
        delay=p.delay_steps,
    )


def make_state(brain: Brain, num: Callable[[float], Any]) -> State:
    s = brain.state
    return State(
        step=s.step,
        v=[num(x) for x in s.v_mV.tolist()],
        g=[num(x) for x in s.g_mV.tolist()],
        last=s.last_spike_step.tolist(),
        in_flight=[torch.nonzero(row).flatten().tolist() for row in s.in_flight],
    )


def generic_step(net: Net, s: State, hit_inputs: list[bool]) -> list[int]:
    """One 0.1 ms step, in the engine's order (tests/_reference_engine.py)."""
    n = len(s.v)
    active = [(s.step - s.last[i]) >= net.refractory[i] for i in range(n)]
    for i in range(n):
        if active[i]:
            s.v[i] = (s.v[i] - net.v_rest) * net.decay_v + s.g[i] * net.g_to_v + net.v_rest
            s.g[i] = s.g[i] * net.decay_g
    fired = [i for i in range(n) if active[i] and s.v[i] > net.v_th]
    is_fired = [False] * n
    for i in fired:
        s.last[i] = s.step
        is_fired[i] = True
    slot = s.step % net.delay
    arriving, s.in_flight[slot] = s.in_flight[slot], fired
    for j in arriving:
        for k in range(net.row_start[j], net.row_start[j + 1]):
            target = net.post[k]
            if active[target] and not is_fired[target]:
                s.g[target] = s.g[target] + net.weight[k]
    for i, hit in zip(net.inputs, hit_inputs, strict=True):
        if hit and active[i] and not is_fired[i]:
            s.v[i] = s.v[i] + net.kick
    for i in fired:
        s.v[i] = net.v_reset
        s.g[i] = net.v_rest - net.v_rest  # zero in this kind of number
    s.step += 1
    return fired


def poisson_hits(brain: Brain, steps: int) -> list[list[bool]]:
    """The engine's own draws from this moment on (its generator, cloned)."""
    gen = torch.Generator().set_state(brain.state.generator.get_state())
    threshold = RATE_HZ * (PARAMS.dt_ms / 1000.0)
    k = len(brain.input_neurons)
    return [(torch.rand(k, generator=gen, dtype=torch.float64) < threshold).tolist()
            for _ in range(steps)]  # fmt: skip


def main() -> None:
    enable_determinism()
    getcontext().prec = DIGITS
    scenario = small()
    brain = scenario.brain(0)
    run_schedule(brain, 1_000)  # a busy moment
    brain.set_input_rates(RATE_HZ)
    hits = poisson_hits(brain, RUN_STEPS)

    # 1. Validate: Python floats must match the engine bit for bit.
    net_f = make_net(brain, float, exact=False)
    state = make_state(brain, float)
    engine = brain.fork()
    mismatched_spikes = 0
    for t in range(VALIDATE_STEPS):
        mismatched_spikes += generic_step(net_f, state, hits[t]) != engine.step().tolist()
    same_v = state.v == engine.state.v_mV.tolist()
    same_g = state.g == engine.state.g_mV.tolist()
    print(f"validation over {VALIDATE_STEPS} steps: voltages identical {same_v}, inputs "
          f"identical {same_g}, steps with different spikes {mismatched_spikes}")  # fmt: skip

    # 2. Two pasts, in float64 and at 50 digits.
    altered = brain.fork()
    blur(altered.state, Knowledge("voltage", SIGMA_MV, seed=0))
    net_d = make_net(brain, Decimal, exact=True)
    runs = {
        "float64": (make_state(brain, float), make_state(altered, float), net_f),
        f"{DIGITS} digits": (make_state(brain, Decimal), make_state(altered, Decimal), net_d),
    }
    rows: list[dict[str, object]] = []
    spikes_differ = {name: 0 for name in runs}
    for t in range(RUN_STEPS):
        for name, (a, b, net) in runs.items():
            spikes_differ[name] += generic_step(net, a, hits[t]) != generic_step(net, b, hits[t])
        if (t + 1) % SAMPLE_STEPS == 0:
            row: dict[str, object] = {"time_ms": (t + 1) // 10}
            for name, (a, b, _) in runs.items():
                row[f"max_dv_mV_{name.replace(' ', '_')}"] = float(
                    max(abs(x - y) for x, y in zip(a.v, b.v, strict=True))
                )
            rows.append(row)
    for name, trace in quiet_neuron(net_f, net_d).items():
        for row, value in zip(rows, trace, strict=True):
            row[f"quiet_neuron_from_rest_mV_{name.replace(' ', '_')}"] = value
    ASSETS.mkdir(parents=True, exist_ok=True)
    out = ASSETS / "exact_check.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for r in rows[:: len(rows) // 10]:
        print(r)
    print(rows[-1])
    print(f"steps where the two pasts spiked differently: {spikes_differ}")
    print(f"wrote {out.name}")


def quiet_neuron(net_f: Net, net_d: Net) -> dict[str, list[float]]:
    """Exploratory (not in the plan): one neuron at rest, nudged 10⁻⁹ mV, no input, 1 s.

    The test network above is busy, so it shows only one side of rounding: a busy
    neuron absorbs a tiny difference outright. The whole brain is mostly quiet,
    which shows the other side: near rest the leak's tiny steps round away.
    """
    traces: dict[str, list[float]] = {}
    for name, net, num in (("float64", net_f, float), (f"{DIGITS} digits", net_d, Decimal)):
        v_rest = net.v_rest
        v = v_rest + num(SIGMA_MV)
        trace = []
        for t in range(1, RUN_STEPS + 1):
            v = (v - v_rest) * net.decay_v + v_rest  # the engine's update with no input
            if t % SAMPLE_STEPS == 0:
                trace.append(float(v - v_rest))
        print(f"one quiet neuron, {name}: distance from rest at 1 s {trace[-1]:.2e} mV")
        traces[name] = trace
    return traces


if __name__ == "__main__":
    main()
