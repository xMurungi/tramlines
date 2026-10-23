"""Find the edges: how faint must a bitter taste or a shadow be for the fly to be undecided?

A decision point is a moment where the brain sits near a decoder threshold, so
small differences decide the outcome (ADR-0031, ADR-0032). Two sweeps, each over
seeds, with the walking drive on as in the real fly:

- laced food: sugar at full strength plus bitter at strength s → does MN9 cross the
  30 Hz "start feeding" threshold in a 50 ms window?
- faint shadow: LPLC2 (one side) ramped 0 → 200·s Hz over 500 ms → does the Giant
  Fiber cross the 50 Hz "jump" threshold?

    uv run python scripts/calibrate_decisions.py
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor

import torch

from tramlines.brain.connectome import Connectome, load_connectome
from tramlines.brain.engine import Brain, enable_determinism
from tramlines.brain.neurons import load_catalog
from tramlines.world.decoder import GIANT_FIBER_JUMP_HZ, MN9_FEED_START_HZ, WINDOW_MS, FlyDecoder
from tramlines.world.senses import BITTER_HZ, LOOM_MAX_HZ, SUGAR_HZ, WALK_DRIVE_HZ, FlySenses

SEEDS = range(6)
BITTER_STRENGTHS = (0.3, 0.4, 0.5, 0.6, 0.7)
LOOM_STRENGTHS = (0.15, 0.2, 0.3, 0.4, 0.5)
STEPS_PER_MS = 10

_connectome: Connectome | None = None


def peak_window_rate(counts_per_ms: list[int]) -> float:
    """Highest firing rate over any 50 ms window, in Hz."""
    best = max(
        sum(counts_per_ms[i : i + WINDOW_MS]) for i in range(len(counts_per_ms) - WINDOW_MS + 1)
    )
    return best * 1000.0 / WINDOW_MS


def trial(job: tuple[str, float, int]) -> tuple[str, float, int, float]:
    global _connectome
    kind, strength, seed = job
    enable_determinism()
    if _connectome is None:
        _connectome = load_connectome()
    catalog = load_catalog()
    senses = FlySenses.from_catalog(catalog)
    decoder = FlyDecoder.from_catalog(catalog)
    brain = Brain(_connectome, senses.input_neurons, seed=seed)
    ports = [senses.sugar, senses.bitter, senses.loom_left, senses.loom_right, senses.walk_drive]

    def rates(sugar: float, bitter: float, loom_right: float) -> torch.Tensor:
        per_port = (sugar, bitter, 0.0, loom_right, WALK_DRIVE_HZ)
        return torch.cat(
            [
                torch.full((len(p),), r, dtype=torch.float64)
                for p, r in zip(ports, per_port, strict=True)
            ]
        )

    readouts = decoder.readout_neurons
    watch = readouts[12:14] if kind == "laced food" else readouts[10:12]  # MN9 L,R | GF L,R
    brain.set_input_rates(rates(0.0, 0.0, 0.0))
    brain.run(300 * STEPS_PER_MS)  # walk for 300 ms first, as the fly would
    counts: list[int] = []
    duration_ms = 1000 if kind == "laced food" else 500
    for ms in range(duration_ms):
        if kind == "laced food":
            brain.set_input_rates(rates(SUGAR_HZ, BITTER_HZ * strength, 0.0))
        else:
            brain.set_input_rates(rates(0.0, 0.0, LOOM_MAX_HZ * strength * (ms + 1) / duration_ms))
        record = brain.run(STEPS_PER_MS)
        counts.append(max(record.count(int(n)) for n in watch))
    return kind, strength, seed, peak_window_rate(counts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bitter", type=float, nargs="*", default=list(BITTER_STRENGTHS))
    parser.add_argument("--loom", type=float, nargs="*", default=list(LOOM_STRENGTHS))
    args = parser.parse_args()
    jobs = [("laced food", s, seed) for s in args.bitter for seed in SEEDS]
    jobs += [("faint shadow", s, seed) for s in args.loom for seed in SEEDS]
    results: dict[tuple[str, float], list[float]] = {}
    with ProcessPoolExecutor(max_workers=2) as pool:  # memory rule (ADR-0029, ADR-0032)
        for kind, strength, _seed, peak in pool.map(trial, jobs):
            results.setdefault((kind, strength), []).append(peak)
    for (kind, strength), peaks in results.items():
        threshold = MN9_FEED_START_HZ if kind == "laced food" else GIANT_FIBER_JUMP_HZ
        crossed = sum(p > threshold for p in peaks)
        span = f"{min(peaks):5.0f}-{max(peaks):5.0f} Hz"
        print(f"{kind:12} strength {strength:4.2f}: peak 50-ms rate {span};"
              f" crosses {threshold:.0f} Hz in {crossed}/{len(peaks)} seeds")  # fmt: skip


if __name__ == "__main__":
    main()
