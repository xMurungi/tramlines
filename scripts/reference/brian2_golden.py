"""Make golden files: small random networks run by Brian2, the reference simulator.

Brian2 is not a project dependency. Run this in a throwaway environment:

    uv run --no-project --python 3.12 --with brian2 --with numpy \\
        python scripts/reference/brian2_golden.py tests/golden

Each network uses the reference model exactly as Shiu et al.'s `model.py` defines it.
Inputs are made deterministic (Poisson rate 10 kHz, so p = 1 per step) and initial
voltages and conductances are random, so the run is rich but has no randomness.
`tests/test_engine_vs_brian2.py` checks our engine reproduces every spike (ADR-0016).
"""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

import numpy as np
from brian2 import (
    Hz,
    Network,
    NeuronGroup,
    PoissonInput,
    SpikeMonitor,
    Synapses,
    defaultclock,
    ms,
    mV,
    prefs,
)

N_NEURONS = 400
N_CANDIDATE_EDGES = 8000
DURATION_MS = 500.0
INPUT_RATE_HZ = 10_000.0  # p = rate * dt = 1: an input event every step


def make_network(seed: int) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    pre = rng.integers(0, N_NEURONS, N_CANDIDATE_EDGES)
    post = rng.integers(0, N_NEURONS, N_CANDIDATE_EDGES)
    keep = pre != post
    pairs = np.unique(np.stack([pre[keep], post[keep]], 1), axis=0)
    signs = np.where(rng.random(len(pairs)) < 0.65, 1, -1)
    return {
        "pre": pairs[:, 0],
        "post": pairs[:, 1],
        "signed_synapses": rng.integers(1, 12, len(pairs)) * signs,
        "v0_mV": rng.uniform(-60, -44.5, N_NEURONS),
        "g0_mV": rng.uniform(-3, 6, N_NEURONS),
        "inputs": np.sort(rng.choice(N_NEURONS, 4, replace=False)),
    }


def run_brian2(net: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    prefs.codegen.target = "numpy"
    defaultclock.dt = 0.1 * ms
    namespace = {"v_0": -52 * mV, "v_rst": -52 * mV, "v_th": -45 * mV, "t_mbr": 20 * ms}
    namespace["tau"] = 5 * ms
    eqs = dedent("""
        dv/dt = (v_0 - v + g) / t_mbr : volt (unless refractory)
        dg/dt = -g / tau               : volt (unless refractory)
        rfc                            : second
    """)
    neurons = NeuronGroup(
        N_NEURONS,
        eqs,
        method="linear",
        threshold="v > v_th",
        reset="v = v_rst; w = 0; g = 0 * mV",
        refractory="rfc",
        namespace=namespace,
    )
    neurons.v = net["v0_mV"] * mV
    neurons.g = net["g0_mV"] * mV
    neurons.rfc = 2.2 * ms
    synapses = Synapses(neurons, neurons, "w : volt", on_pre="g += w", delay=1.8 * ms)
    synapses.connect(i=net["pre"], j=net["post"])
    synapses.w = net["signed_synapses"] * 0.275 * mV
    inputs = []
    for i in net["inputs"]:
        target = neurons[int(i) : int(i) + 1]
        inputs.append(PoissonInput(target, "v", N=1, rate=INPUT_RATE_HZ * Hz, weight=68.75 * mV))
        neurons[int(i)].rfc = 0 * ms
    monitor = SpikeMonitor(neurons)
    Network(neurons, synapses, monitor, *inputs).run(DURATION_MS * ms)
    return {
        "spike_neurons": np.asarray(monitor.i[:], dtype=np.int64),
        "spike_steps": np.round(np.asarray(monitor.t[:] / defaultclock.dt)).astype(np.int64),
        "v_end_mV": np.asarray(neurons.v[:] / mV),
        "g_end_mV": np.asarray(neurons.g[:] / mV),
    }


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for seed in (1, 2):
        net = make_network(seed)
        result = run_brian2(net)
        np.savez_compressed(out / f"brian2_net{seed}.npz", **net, **result)
        print(f"net {seed}: {len(result['spike_steps'])} spikes")


if __name__ == "__main__":
    main()
