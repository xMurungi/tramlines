"""The free-will fan: aiming, measuring, the ghost worker and the server's bookkeeping (ADR-0046).

Everything runs in this process on the small 400-neuron network (tests/_scenarios.py), so
nothing here needs the FlyWire data or a second brain process.
"""

import json
import queue
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
from _scenarios import PROBE_ARENA, timeline_small
from fastapi.testclient import TestClient
from pydantic import TypeAdapter, ValidationError

from tramlines.brain.data import DATA_DIR
from tramlines.brain.neurons import ANNOTATIONS_FILE
from tramlines.server import app as server
from tramlines.server import workers
from tramlines.server.fans import BRANCHES, FAN, DecisionLog, decision_at, fan_key
from tramlines.server.jobs import GhostJobs, Job
from tramlines.server.knowledge import CONTROL
from tramlines.server.protocol import (
    AimedSpike,
    Choose,
    FanBranch,
    FreeWill,
    Hello,
    SpikeRefused,
    ViewerMessage,
)
from tramlines.server.workers import checkpoint_path, run_ghost, run_projector
from tramlines.timeline import branches
from tramlines.timeline.divergence import brain_difference
from tramlines.timeline.timeline import Pose, Timeline
from tramlines.world.arena import Arena, Loom, Patch

PoseRow = tuple[int, float, float, float, bool, bool]
HORIZON_MS = 100


def rows(start: int, end: int, x0: float = 0.0) -> list[PoseRow]:
    return [(t, x0 + t * 0.01, 0.0, 0.0, False, False) for t in range(start, end)]


def small_at(ms: int, seed: int = 3) -> Timeline:
    timeline = timeline_small().timeline(seed)
    timeline.run(ms)
    return timeline


# --- Aiming the spikes (tramlines.timeline.branches) ---


def test_each_branch_gets_one_spike_in_a_different_driven_neuron() -> None:
    timeline = small_at(100)
    driven = set(branches.driven_neurons(timeline).tolist())
    rates = timeline.senses.rates_hz(timeline.fly, timeline.arena)
    assert driven == set(timeline.brain.input_neurons[rates > 0].tolist()) and driven
    aim = branches.aim(timeline, BRANCHES, seed=100)
    neurons = [k for k, _ in aim.branches]
    assert len(neurons) == BRANCHES == len(set(neurons))
    assert set(neurons) <= driven
    assert aim.driven == len(driven)
    for neuron, twin in aim.branches:
        # The spike is really there: the neuron has just fired and its spike is in transit.
        step = twin.brain.state.step - 1
        assert int(twin.brain.state.last_spike_step[neuron]) == step
        assert bool(twin.brain.state.in_flight[step % twin.brain.params.delay_steps, neuron])
        assert twin.fingerprint() != timeline.fingerprint()  # never a silent copy


def test_aiming_is_repeatable_and_leaves_the_moment_untouched() -> None:
    timeline = small_at(100)
    before = timeline.fingerprint()
    first = [k for k, _ in branches.aim(timeline, BRANCHES, seed=100).branches]
    assert timeline.fingerprint() == before  # forks only; the brain's own random stream unused
    assert [k for k, _ in branches.aim(timeline, BRANCHES, seed=100).branches] == first
    assert [k for k, _ in branches.aim(timeline, BRANCHES, seed=101).branches] != first


def test_a_neuron_that_just_fired_is_refused_and_replaced_never_copied() -> None:
    timeline = timeline_small().timeline(3)
    # Step until some driven input neuron fired at the last brain step (inputs have no
    # refractory period, so only inject_spike's own check stops it, ADR-0041).
    while True:
        timeline.step()
        just_now = timeline.brain.state.step - 1
        driven = branches.driven_neurons(timeline)
        fired = [int(k) for k in driven if int(timeline.brain.state.last_spike_step[k]) == just_now]
        if fired and timeline.fly.time_ms > 5:
            break
    aim = branches.aim(timeline, len(driven), seed=7)  # try every driven neuron
    refused = {r.neuron: r.reason for r in aim.refused}
    assert set(fired) <= set(refused)
    assert all("already fired" in refused[k] for k in fired)
    assert not set(refused) & {k for k, _ in aim.branches}
    assert len(aim.branches) + len(aim.refused) == len(driven)


def test_with_too_few_driven_neurons_the_fan_is_smaller_and_says_so() -> None:
    aim = branches.aim(small_at(50), 1000, seed=0)
    assert len(aim.branches) + len(aim.refused) == aim.driven < 1000


# --- Measuring the futures ---


def test_the_untouched_future_is_the_moment_run_on_bit_for_bit() -> None:
    timeline = small_at(100)
    untouched = branches.run_untouched(timeline, HORIZON_MS)
    assert untouched.poses == timeline.run(HORIZON_MS)
    assert untouched.timeline.fingerprint() == timeline.fingerprint()


def test_a_branch_is_measured_against_the_untouched_future() -> None:
    timeline = small_at(100)
    aim = branches.aim(timeline, BRANCHES, seed=100)
    untouched = branches.run_untouched(timeline, HORIZON_MS)
    for neuron, twin in aim.branches:
        alone = twin.fork()  # the same branch, run separately, to check the measurement
        branch = branches.run_branch(neuron, twin, untouched, HORIZON_MS)
        poses, _ = alone.run_recording(HORIZON_MS)
        assert branch.poses == poses
        assert len(branch.distance_mm) == HORIZON_MS
        assert len(branch.spike_diffs) == HORIZON_MS // branches.SPIKE_BIN_MS
        # The extra spike always changes the brain's raster on this busy network.
        assert sum(branch.spike_diffs) > 0
        expected = brain_difference(twin.brain, untouched.timeline.brain)
        assert branch.brain_at_end == expected
        assert branch.brain_rejoined == expected.below(branches.BRAIN_SAME_WITHIN_MV)
        apart = [t + 1 for t, d in enumerate(branch.distance_mm) if d > branches.APART_MM]
        assert branch.first_apart_ms == (apart[0] if apart else None)


def pose(t: int, x: float, feeding: bool = False, jumped: bool = False) -> Pose:
    return Pose(t, x, 0.0, 0.0, feeding, jumped)


def branch_with(distance: list[float], same_feeding: bool = True) -> branches.Branch:
    first = next((t + 1 for t, d in enumerate(distance) if d > branches.APART_MM), None)
    nothing = branches.BrainDifference(0.0, 0.0, True)
    return branches.Branch(0, [], distance, [], first, nothing, same_feeding)


def test_which_branches_rejoin_and_which_never_do() -> None:
    assert not branch_with([0.0, 0.05, 0.0]).split  # never left the untouched path
    rejoined = branch_with([0.0, 0.5, 0.05])
    assert rejoined.split and rejoined.body_rejoined
    assert not branch_with([0.0, 0.5, 0.5]).body_rejoined  # split for good
    # Back in the same place but one fly feeding and the other not: not rejoined.
    assert not branch_with([0.0, 0.5, 0.05], same_feeding=False).body_rejoined
    assert branch_with([0.0]).brain_rejoined
    different = branches.BrainDifference(1e-6, 0.0, True)
    assert not branches.Branch(0, [], [0.0], [], None, different, True).brain_rejoined


def test_events_say_when_the_fly_feeds_stops_and_jumps() -> None:
    poses = [pose(1, 0, True), pose(2, 0, True), pose(3, 0, False, jumped=True), pose(4, 0)]
    assert branches.events(poses, feeding_before=False) == [
        (1, "feeds"),
        (3, "jumps"),
        (3, "stops feeding"),
    ]


# --- When free will is offered ---

ARENA = Arena(
    radius_mm=40.0,
    patches=(
        Patch(10.0, 0.0, 2.0, "food"),
        Patch(10.0, 0.0, 2.0, "bitter", strength=0.5),
        Patch(-10.0, 0.0, 2.0, "bitter"),
        Patch(0.0, 10.0, 2.0, "food", strength=0.0),
    ),
    looms=(Loom(start_ms=500, duration_ms=100, direction_rad=0.0),),
)


def at(t: int, x: float, y: float = 0.0) -> PoseRow:
    return (t, x, y, 0.0, False, False)


def test_decision_moments_are_food_bitter_laced_food_and_shadows() -> None:
    assert decision_at(at(1, 0.0), ARENA) is None  # only walking
    assert decision_at(at(1, 10.0), ARENA) == "on laced food"
    assert decision_at(at(1, -10.0), ARENA) == "on bitter"
    assert decision_at(at(1, 0.0, 10.0), ARENA) is None  # a patch of strength 0 is nothing
    assert decision_at(at(550, 0.0), ARENA) == "a shadow approaching"
    assert decision_at(at(499, 0.0), ARENA) is None  # the shadow has not begun
    assert decision_at(at(600, 0.0), ARENA) is None  # and it has gone


def test_the_decision_log_keeps_runs_of_moments() -> None:
    log = DecisionLog(ARENA)
    assert not log.add([at(t, 0.0) for t in range(1, 10)])
    assert log.add([at(t, 10.0) for t in range(10, 20)] + [at(20, 0.0), at(21, -10.0)])
    assert not log.add([at(15, 10.0)])  # already seen
    assert log.moments == [(10, 19, "on laced food"), (21, 21, "on bitter")]
    assert log.at(12) == "on laced food" and log.at(20) is None


# --- Messages ---


def test_a_viewer_sends_choose_or_free_will_and_nothing_else() -> None:
    adapter: TypeAdapter[Choose | FreeWill] = TypeAdapter(ViewerMessage)
    request = adapter.validate_json('{"type": "free_will", "at_ms": 1200}')
    assert isinstance(request, FreeWill) and request.at_ms == 1200
    assert isinstance(adapter.validate_json('{"type": "choose", "knowledge": "control"}'), Choose)
    for bad in ('{"type": "free_will", "at_ms": 0}', '{"type": "free_will"}', '{"at_ms": 5}'):
        with pytest.raises(ValidationError):
            adapter.validate_json(bad)


# --- The ghost worker, on the small network ---


@pytest.fixture
def projected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """300 ms of the small timeline, checkpointed every 100 ms."""
    monkeypatch.setattr(workers, "CHECKPOINT_EVERY_MS", 100)
    scenario = timeline_small()
    out: queue.Queue[tuple[Any, ...]] = queue.Queue()

    def parts() -> workers.Parts:
        return scenario.connectome, scenario.senses, scenario.decoder

    run_projector(out, tmp_path, PROBE_ARENA, seed=3, duration_ms=300, parts=parts)
    live = {row[0]: row for m in out.queue if m[0] == "chunk" for row in m[2]}
    return {"dir": tmp_path, "parts": parts, "live": live}


def worker_answers(projected: dict[str, Any], jobs: list[Job]) -> list[tuple[Any, ...]]:
    inbox: queue.Queue[Job | None] = queue.Queue()
    for job in [*jobs, None]:
        inbox.put(job)
    out: queue.Queue[tuple[Any, ...]] = queue.Queue()
    run_ghost(inbox, out, PROBE_ARENA, horizon_ms=HORIZON_MS, parts=projected["parts"])
    return list(out.queue)


def test_the_worker_streams_a_fan_from_the_checkpoint_behind_the_moment(
    projected: dict[str, Any],
) -> None:
    at_ms = 137  # between checkpoints: the worker runs on from 100 ms to 137 ms first
    path = str(checkpoint_path(projected["dir"], 100))
    answers = worker_answers(projected, [(FAN, at_ms, path)])
    kinds = [a[0] for a in answers]
    assert kinds == ["fan_plan", "fan_base"] + ["branch"] * BRANCHES + ["fan_done", "ghost_done"]
    _, plan_ms, driven, aimed, refused = answers[0]
    assert plan_ms == at_ms and driven == 20 and len(aimed) == BRANCHES and refused == []
    assert all(isinstance(a, AimedSpike) and a.label.startswith("input neuron") for a in aimed)
    # The untouched future, computed by the ghost process, is the live fly bit for bit.
    base = answers[1][2]
    assert [tuple(p) for p in base] == [projected["live"][t] for t in range(138, 238)]

    # Each branch is exactly what the library gives, run by hand from the same moment.
    by_hand = timeline_small().load(Path(path))
    by_hand.run(at_ms - 100)
    aim = branches.aim(by_hand, BRANCHES, seed=at_ms)
    untouched = branches.run_untouched(by_hand, HORIZON_MS)
    for index, ((neuron, twin), answer) in enumerate(zip(aim.branches, answers[2:10], strict=True)):
        sent: FanBranch = answer[1]
        expected = branches.run_branch(neuron, twin, untouched, HORIZON_MS)
        assert (sent.at_ms, sent.index, sent.neuron) == (at_ms, index, neuron)
        assert sent.label == aimed[index].label
        assert sent.poses == [workers.pose_row(p) for p in expected.poses[9::10]]
        assert sent.distance_mm == expected.distance_mm[9::10]
        assert sent.spike_diffs == expected.spike_diffs
        assert sent.brain_rejoined == expected.brain_rejoined
        assert sent.end_distance_mm == expected.distance_mm[-1]


def test_the_worker_names_the_flys_senses_by_type_and_root_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tramlines.brain.neurons import NeuronCatalog
    from tramlines.world.senses import FlySenses

    def ports(*ks: int) -> torch.Tensor:
        return torch.tensor(ks, dtype=torch.int64)

    senses = FlySenses(ports(0), ports(1), ports(2), ports(3), ports(4))
    import pandas as pd

    annotations = pd.DataFrame({"cell_type": ["CB2777"]}, index=pd.Index([1004], name="root_id"))
    catalog = NeuronCatalog(np.array([1000, 1001, 1002, 1003, 1004]), annotations)
    monkeypatch.setattr(workers, "_catalog", lambda: catalog)
    assert workers.describe_input(senses, 4) == "walking drive · CB2777 · 1004"
    assert workers.describe_input(senses, 0) == "sugar taste · unnamed type · 1000"


# --- The server's bookkeeping, with a stand-in for the processes ---


class FakeWorkers:
    def __init__(self) -> None:
        self.out: queue.Queue[tuple[Any, ...]] = queue.Queue()
        self.sent: list[Job] = []

    def send(self, job: Job) -> None:
        self.sent.append(job)

    def dead(self) -> list[str]:
        return []


@pytest.fixture
def run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> server.Run:
    monkeypatch.setattr(server, "PROJECTIONS", tmp_path)
    monkeypatch.setattr(server, "build_fingerprint", lambda: "test")
    monkeypatch.setitem(server.ARENAS, "decision", ARENA)
    return server.Run(settings=server.Settings(), hello=None)  # type: ignore[arg-type]


def checkpoint(run: server.Run, at_ms: int, fake: FakeWorkers) -> None:
    run.settings.checkpoints.mkdir(parents=True, exist_ok=True)
    checkpoint_path(run.settings.checkpoints, at_ms).touch()
    run.accept(("checkpoint", at_ms, 1), fake)


def on_laced_food(start: int, end: int) -> list[PoseRow]:
    return [(t, 10.0, 0.0, 0.0, False, False) for t in range(start, end)]


def a_branch(at_ms: int, index: int) -> FanBranch:
    return FanBranch(
        at_ms=at_ms, index=index, neuron=10 + index, label=f"input neuron {10 + index}",
        poses=[], distance_mm=[0.0, 0.5], spike_diffs=[3], spike_bin_ms=100,
        first_apart_ms=20, end_distance_mm=0.5, max_distance_mm=0.5, split=True,
        body_rejoined=False, brain_rejoined=index == 0, brain_max_dv_mV=0.0, events=[],
    )  # fmt: skip


def messages(outbox: Any) -> list[dict[str, Any]]:
    return [json.loads(outbox.get_nowait()) for _ in range(outbox.qsize())]


def test_free_will_is_refused_away_from_decision_moments(run: server.Run) -> None:
    fake = FakeWorkers()
    checkpoint(run, 0, fake)
    run.accept(("chunk", 0, rows(1, 101), np.array([1]), 1), fake)  # walking only
    refusal = run.free_will(FreeWill(at_ms=50), fake)
    assert refusal is not None and refusal.done and "decision moments" in (refusal.not_made or "")
    assert run.fans.records == {} and run.jobs.fans_remaining() == 0


def test_a_fan_goes_first_is_logged_cached_and_checked_against_the_live_fly(
    run: server.Run,
) -> None:
    fake = FakeWorkers()
    outbox: Any = queue.Queue()
    run.outboxes.add(outbox)  # type: ignore[arg-type]
    checkpoint(run, 0, fake)
    assert fake.sent == [(CONTROL, 0, str(checkpoint_path(run.settings.checkpoints, 0)))]
    run.accept(("chunk", 0, on_laced_food(1, 101), np.array([1]), 1), fake)
    checkpoint(run, 100, fake)
    run.choose(Choose(knowledge="float32", from_ms=0), fake)
    assert run.free_will(FreeWill(at_ms=60), fake) is None
    assert run.status().fans_to_compute == 1
    run.accept(("ghost", CONTROL, 0, on_laced_food(1, 101)), fake)
    # The fan jumps the queue of waiting ghosts, from the checkpoint behind it.
    assert fake.sent[-1] == (FAN, 60, str(checkpoint_path(run.settings.checkpoints, 0)))
    assert run.free_will(FreeWill(at_ms=60), fake) is None  # asked again: not queued twice
    assert len(fake.sent) == 2

    aimed = [AimedSpike(neuron=10 + i, label=f"input neuron {10 + i}") for i in range(2)]
    refused = [SpikeRefused(neuron=9, label="input neuron 9", reason="already fired")]
    run.accept(("fan_plan", 60, 20, aimed, refused), fake)
    base = on_laced_food(61, 101) + on_laced_food(101, 161)  # second half not yet computed
    run.accept(("fan_base", 60, base), fake)
    run.accept(("branch", a_branch(60, 0)), fake)
    run.accept(("branch", a_branch(60, 1)), fake)
    fan = run.fans.records[60].fan
    assert (fan.decision, fan.driven, fan.checkpoint_ms) == ("on laced food", 20, 0)
    assert (fan.base_compared_ms, fan.base_matched_ms) == (40, 40)
    run.accept(("fan_done", 60), fake)
    assert fan.done and run.status().fans_to_compute == 0
    assert fake.sent[-1][0] == "float32"  # then the waiting ghosts carry on

    # The rest of the live fly arrives: the untouched future is checked as it comes.
    run.accept(("chunk", 100, on_laced_food(101, 201), np.array([1]), 1), fake)
    assert (fan.base_compared_ms, fan.base_matched_ms) == (100, 100)

    sent = messages(outbox)
    assert any(m["type"] == "decisions" and m["moments"][0][2] == "on laced food" for m in sent)
    assert [m["index"] for m in sent if m["type"] == "branch"] == [0, 1]

    path = server.fan_path(run.settings, 60)
    assert path.exists() and fan_key() in path.name and "t0000060" in path.name
    saved = json.loads(path.read_text())
    assert saved["fan"]["refused"] == [
        {"neuron": 9, "label": "input neuron 9", "reason": "already fired"}
    ]
    assert len(saved["branches"]) == 2 and len(saved["base"]) == len(base)

    # A restart replays the fan from disk and re-checks it against the cached live fly.
    run.accept(("projector_done",), fake)
    run.accept(("ghost", "float32", 0, on_laced_food(1, 101)), fake)
    run.accept(("ghost", CONTROL, 100, on_laced_food(101, 201)), fake)
    assert server.cache_path(run.settings).exists()
    hello = Hello.describe("decision", ARENA, 0, HORIZON_MS, 200, np.zeros((3, 2)))
    again = server.Run(settings=run.settings, hello=hello)
    assert server.load_cache(again)
    replayed = again.fans.records[60]
    assert replayed.fan.done and sorted(replayed.branches) == [0, 1]
    assert (replayed.fan.base_compared_ms, replayed.fan.base_matched_ms) == (100, 100)
    assert again.jobs.fans_remaining() == 0
    assert again.decision_log.at(60) == "on laced food"
    snapshot = [json.loads(m)["type"] for m in again.snapshot()]
    assert snapshot.count("fan") == 1 and snapshot.count("branch") == 2


def test_a_fan_with_nothing_to_aim_at_says_so(run: server.Run) -> None:
    fake = FakeWorkers()
    checkpoint(run, 0, fake)
    run.accept(("chunk", 0, on_laced_food(1, 101), np.array([1]), 1), fake)
    run.free_will(FreeWill(at_ms=10), fake)
    run.accept(("fan_plan", 10, 0, [], []), fake)
    run.accept(("fan_done", 10), fake)
    assert "no neuron" in (run.fans.records[10].fan.not_made or "")


def test_a_fan_whose_saved_moment_is_missing_is_refused_not_sent(run: server.Run) -> None:
    fake = FakeWorkers()
    run.accept(("checkpoint", 0, 3), fake)  # no file behind it
    run.accept(("chunk", 0, on_laced_food(1, 101), np.array([1]), 1), fake)
    run.free_will(FreeWill(at_ms=10), fake)
    assert fake.sent == []
    assert "missing" in (run.fans.records[10].fan.not_made or "")


def test_the_latest_fan_asked_for_goes_first() -> None:
    jobs = GhostJobs()
    jobs.add_checkpoint(0, Path("t0.pt"))
    jobs.want_fan(10, Path("t0.pt"))
    jobs.want_fan(20, Path("t0.pt"))
    jobs.want_fan(10, Path("t0.pt"))  # asked again: now the latest
    order = []
    while (job := jobs.next()) is not None:
        order.append(job[:2])
        jobs.mark_done(job[0], job[1])
    assert order == [(FAN, 10), (FAN, 20), (CONTROL, 0)]


@pytest.mark.skipif(not (DATA_DIR / ANNOTATIONS_FILE).exists(), reason="needs fetch_data.py")
def test_a_viewer_asking_away_from_a_decision_hears_why_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TRAMLINES_ARENA", "default")
    monkeypatch.setenv("TRAMLINES_SECONDS", "0.1")
    monkeypatch.setenv("TRAMLINES_HORIZON_MS", "100")
    monkeypatch.setattr(server, "PROJECTIONS", tmp_path)
    cached = {
        "chunks": [{"t0_ms": 0, "poses": rows(1, 101), "fired": "", "spikes": 0}],
        "checkpoints": [[0, 2]],
        "ghosts": [[0, rows(1, 101)]],
    }
    (tmp_path / f"{server.Settings().key}.json").write_text(json.dumps(cached))
    with TestClient(server.app) as client, client.websocket_connect("/stream") as ws:
        first = [json.loads(ws.receive_text())["type"] for _ in range(6)]
        assert "decisions" not in first  # this run has no decision moments to offer
        ws.send_text(json.dumps({"type": "free_will", "at_ms": 50}))
        reply = json.loads(ws.receive_text())
    assert (reply["type"], reply["at_ms"], reply["done"]) == ("fan", 50, True)
    assert "decision moments" in reply["not_made"]
