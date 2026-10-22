"""The sacred tests (CLAUDE.md 13.2, ADR-0022). Never weaken, skip or mark these flaky.

Two timelines that start from the same state and receive the same inputs must be
identical, bit for bit, forever. Three ways to start from "the same state":

  (a) fork:          a copy made in memory mid-run;
  (b) fresh process: the same seed in a new interpreter;
  (c) save/load:     a copy written to disk and read back.

Each is proved for the brain alone and for a whole timeline (brain + fly + world).

"Identical" means equal SHA-256 fingerprints of the whole spike raster and of
every bit of the final state, random generator included.

Each property runs for 10 seeds. Set TRAMLINES_DETERMINISM_REPEATS=10 to repeat
everything 10 times: the Phase 2 gate (100/100 per property).
"""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from _scenarios import (
    HAVE_DATA,
    Scenario,
    TimelineScenario,
    by_name,
    run,
    timeline_by_name,
)

from tramlines.brain.connectome import from_arrays
from tramlines.brain.engine import Brain
from tramlines.timeline.timeline import Timeline

SEEDS = range(10)
REPEATS = range(int(os.environ.get("TRAMLINES_DETERMINISM_REPEATS", "1")))
SCENARIOS = [
    "small",
    pytest.param(
        "full",
        marks=pytest.mark.skipif(not HAVE_DATA, reason="full brain needs fetch_data.py"),
    ),
]
CHILD = Path(__file__).with_name("_determinism_child.py")


def fingerprints(brain: Brain, scenario: Scenario) -> tuple[str, str]:
    record = run(brain, scenario.total_steps)
    assert record.neurons.numel() > 0, "a silent run would prove nothing"
    return record.fingerprint(), brain.state.fingerprint()


@pytest.mark.parametrize("repeat", REPEATS)
@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", SCENARIOS)
def test_a_fork_is_identical(name: str, seed: int, repeat: int) -> None:
    scenario = by_name(name)
    original = scenario.brain(seed)
    run(original, scenario.fork_step(seed))
    twin = original.fork()
    assert twin.connectome is original.connectome  # wiring shared, not copied (ADR-0008)
    assert twin.state.v_mV.data_ptr() != original.state.v_mV.data_ptr()
    assert fingerprints(twin, scenario) == fingerprints(original, scenario)


@pytest.mark.parametrize("repeat", REPEATS)
@pytest.mark.parametrize("name", SCENARIOS)
def test_b_fresh_process_is_identical(name: str, repeat: int) -> None:
    scenario = by_name(name)
    here = {seed: fingerprints(scenario.brain(seed), scenario) for seed in SEEDS}
    child = subprocess.run(
        [sys.executable, CHILD.name, name, *map(str, SEEDS)],
        cwd=CHILD.parent,
        capture_output=True,
        text=True,
        check=True,
    )
    there = {int(s): (r, f) for s, r, f in (line.split() for line in child.stdout.splitlines())}
    assert there == here


@pytest.mark.parametrize("repeat", REPEATS)
@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", SCENARIOS)
def test_c_save_and_load_is_identical(name: str, seed: int, repeat: int, tmp_path: Path) -> None:
    scenario = by_name(name)
    original = scenario.brain(seed)
    run(original, scenario.fork_step(seed))
    original.save(tmp_path / "state.pt")
    restored = Brain.load(tmp_path / "state.pt", scenario.connectome)
    assert restored.state.fingerprint() == original.state.fingerprint()
    assert fingerprints(restored, scenario) == fingerprints(original, scenario)


# --- The tests can tell when things differ (negative controls) ---


@pytest.mark.parametrize("name", SCENARIOS)
def test_different_randomness_diverges(name: str) -> None:
    scenario = by_name(name)
    original = scenario.brain(0)
    run(original, scenario.fork_step(0))
    twin = original.fork()
    twin.state.generator.manual_seed(12345)
    assert fingerprints(twin, scenario)[0] != fingerprints(original, scenario)[0]


@pytest.mark.parametrize("name", SCENARIOS)
def test_one_extra_spike_diverges(name: str) -> None:
    scenario = by_name(name)
    original = scenario.brain(0)
    run(original, scenario.fork_step(0))
    twin = original.fork()
    neuron = int(scenario.inputs[0])
    twin.state.v_mV[neuron] = 0.0  # far above threshold: fires on the next step
    assert fingerprints(twin, scenario)[0] != fingerprints(original, scenario)[0]


# --- Forks really are independent ---


def test_fork_does_not_touch_the_original() -> None:
    scenario = by_name("small")
    original = scenario.brain(0)
    run(original, 500)
    before = original.state.fingerprint()
    wiring = original.connectome.fingerprint
    twin = original.fork()
    twin.set_input_rates(999.0)
    run(twin, 1500)
    assert original.state.fingerprint() == before
    assert original.connectome.fingerprint == wiring
    assert torch.equal(original.refractory_steps, twin.refractory_steps)


def test_load_refuses_different_wiring(tmp_path: Path) -> None:
    scenario = by_name("small")
    brain = scenario.brain(0)
    brain.save(tmp_path / "state.pt")
    other = from_arrays(400, np.array([0]), np.array([1]), np.array([1]))
    with pytest.raises(ValueError, match="different connectome"):
        Brain.load(tmp_path / "state.pt", other)


# --- Timelines: the brain, the fly's body and the world, forked as one (ADR-0025) ---

TIMELINES = [
    "timeline-small",
    pytest.param(
        "timeline-full",
        marks=pytest.mark.skipif(not HAVE_DATA, reason="full brain needs fetch_data.py"),
    ),
]


def timeline_fingerprints(timeline: Timeline, scenario: TimelineScenario) -> tuple[str, str]:
    poses = timeline.run(scenario.total_ms - timeline.fly.time_ms)
    path = hashlib.sha256(repr(poses).encode()).hexdigest()
    moves = {(p.x_mm, p.y_mm, p.heading_rad) for p in poses}
    assert len(moves) > 1, "a fly that never moves proves nothing"
    return path, timeline.fingerprint()


@pytest.mark.parametrize("repeat", REPEATS)
@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", TIMELINES)
def test_a_timeline_fork_is_identical(name: str, seed: int, repeat: int) -> None:
    scenario = timeline_by_name(name)
    original = scenario.timeline(seed)
    original.run(scenario.fork_ms(seed))
    twin = original.fork()
    assert twin.arena is original.arena and twin.brain.connectome is original.brain.connectome
    assert timeline_fingerprints(twin, scenario) == timeline_fingerprints(original, scenario)


@pytest.mark.parametrize("repeat", REPEATS)
@pytest.mark.parametrize("name", TIMELINES)
def test_b_timeline_fresh_process_is_identical(name: str, repeat: int) -> None:
    scenario = timeline_by_name(name)
    here = {s: timeline_fingerprints(scenario.timeline(s), scenario) for s in SEEDS}
    child = subprocess.run(
        [sys.executable, CHILD.name, name, *map(str, SEEDS)],
        cwd=CHILD.parent,
        capture_output=True,
        text=True,
        check=True,
    )
    there = {int(s): (r, f) for s, r, f in (line.split() for line in child.stdout.splitlines())}
    assert there == here


@pytest.mark.parametrize("repeat", REPEATS)
@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", TIMELINES)
def test_c_timeline_save_and_load_is_identical(
    name: str, seed: int, repeat: int, tmp_path: Path
) -> None:
    scenario = timeline_by_name(name)
    original = scenario.timeline(seed)
    original.run(scenario.fork_ms(seed))
    original.save(tmp_path / "timeline.pt")
    restored = scenario.load(tmp_path / "timeline.pt")
    assert restored.fingerprint() == original.fingerprint()
    assert timeline_fingerprints(restored, scenario) == timeline_fingerprints(original, scenario)


def test_timeline_nudge_changes_the_path() -> None:
    scenario = timeline_by_name("timeline-small")
    original = scenario.timeline(0)
    original.run(scenario.fork_ms(0))
    twin = original.fork()
    twin.fly.heading_rad += 1e-9  # the world, not the brain, is nudged
    assert timeline_fingerprints(twin, scenario)[0] != timeline_fingerprints(original, scenario)[0]
