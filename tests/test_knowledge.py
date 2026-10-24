"""The knowledge slider: settings, messages, scheduling and the ghost worker (ADR-XXXX).

Workers run in this process on the small 400-neuron network (tests/_scenarios.py), so
nothing here needs the FlyWire data or a second brain process.
"""

import json
import queue
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from _scenarios import PROBE_ARENA, timeline_small
from fastapi.testclient import TestClient
from pydantic import ValidationError

from tramlines.brain.data import DATA_DIR
from tramlines.brain.neurons import ANNOTATIONS_FILE
from tramlines.server import app as server
from tramlines.server import workers
from tramlines.server.history import RunHistory
from tramlines.server.jobs import GhostJobs, Job
from tramlines.server.knowledge import BY_ID, CONTROL, RIGHT_WITHIN_MM, SETTINGS, Setting
from tramlines.server.protocol import Choose, Chunk, Hello, encode_indices
from tramlines.server.workers import checkpoint_path, run_ghost, run_projector
from tramlines.timeline.perturb import Knowledge, blur

PoseRow = tuple[int, float, float, float, bool, bool]


def rows(start: int, end: int, x0: float = 0.0) -> list[PoseRow]:
    return [(t, x0 + t * 0.01, 0.0, 0.0, False, False) for t in range(start, end)]


def chunk(start: int, end: int) -> Chunk:
    return Chunk(
        t0_ms=start, poses=rows(start + 1, end + 1), fired=encode_indices(np.array([1])), spikes=1
    )


# --- The settings ---


def test_the_slider_offers_result_1s_settings_with_the_control_first() -> None:
    assert SETTINGS[0].id == CONTROL and SETTINGS[0].knowledge is None
    wanted = {
        Knowledge("voltage", 1e-3),
        Knowledge("voltage", 1e-2),
        Knowledge("voltage", 1e-1),
        Knowledge("float32"),
        Knowledge("partial", 0.999),
        Knowledge("partial", 0.99),
        Knowledge("drop_spike"),
    }
    assert {s.knowledge for s in SETTINGS[1:]} == wanted
    assert len({s.id for s in SETTINGS}) == len(SETTINGS)
    assert [s.id for s in SETTINGS if s.needs_spike_in_transit] == ["drop-spike"]


def test_a_settings_cache_key_changes_with_its_kind_size_and_draw() -> None:
    keys = {s.key for s in SETTINGS}
    assert len(keys) == len(SETTINGS)
    voltage = BY_ID["voltage-0.01"]
    assert voltage.key != replace(voltage, knowledge=Knowledge("voltage", 2e-2)).key
    assert voltage.key != replace(voltage, knowledge=Knowledge("voltage", 1e-2, seed=1)).key


def test_the_control_is_described_as_a_copy() -> None:
    assert "control" in BY_ID[CONTROL].description
    assert BY_ID["voltage-0.01"].description == "voltage known to 0.01 mV"


# --- Messages ---


def test_choose_accepts_only_known_settings() -> None:
    choice = Choose.model_validate_json('{"type": "choose", "knowledge": "voltage-0.1"}')
    assert (choice.knowledge, choice.from_ms) == ("voltage-0.1", 0)
    with pytest.raises(ValidationError):
        Choose.model_validate_json('{"type": "choose", "knowledge": "omniscience"}')
    with pytest.raises(ValidationError):
        Choose.model_validate_json('{"type": "choose", "knowledge": "control", "from_ms": -5}')


def test_hello_lists_the_slider_in_order() -> None:
    hello = Hello.describe("probe", PROBE_ARENA, 0, 100, 300, np.zeros((3, 2)))
    assert [o.id for o in hello.knowledge] == [s.id for s in SETTINGS]
    assert hello.right_within_mm == RIGHT_WITHIN_MM
    assert [o.needs_spike_in_transit for o in hello.knowledge][-1] is True


# --- Scoring an imperfect ghost ---


def test_an_imperfect_ghost_is_scored_on_its_own_track() -> None:
    history = RunHistory()
    history.add_chunk(chunk(0, 100))
    history.add_ghost(0, rows(1, 101))  # the control: exact
    # Right for 40 ms, then 1 mm off: peeled away.
    off = rows(1, 41) + rows(41, 101, x0=1.0)
    history.add_ghost(0, off, knowledge="voltage-0.1")
    control, imperfect = history.match(), history.match("voltage-0.1")
    assert (control.compared_ms, control.matched_ms, control.close_ms) == (100, 100, 100)
    assert (imperfect.compared_ms, imperfect.matched_ms, imperfect.close_ms) == (100, 40, 40)
    assert imperfect.knowledge == "voltage-0.1"
    assert imperfect.right_for == [(0, 40)]  # Result 1's convention: ms before the first miss
    assert control.right_for == [(0, 100)]  # the whole horizon


def test_right_for_waits_until_the_whole_horizon_is_checked() -> None:
    history = RunHistory()
    history.add_ghost(0, rows(1, 201), knowledge="float32")
    history.add_chunk(chunk(0, 100))
    assert history.match("float32").right_for == []  # half checked: not known yet
    history.add_chunk(chunk(100, 200))
    assert history.match("float32").right_for == [(0, 200)]


def test_on_path_uses_result_1s_distance() -> None:
    history = RunHistory()
    history.add_chunk(chunk(0, 100))
    history.add_ghost(0, rows(1, 101, x0=RIGHT_WITHIN_MM * 0.99), knowledge="partial-0.99")
    history.add_ghost(0, rows(1, 101, x0=RIGHT_WITHIN_MM * 1.01), knowledge="partial-0.999")
    assert history.match("partial-0.99").close_ms == 100
    assert history.match("partial-0.999").close_ms == 0


# --- Which ghost next ---


def jobs_with(*at_ms: int) -> GhostJobs:
    jobs = GhostJobs()
    for ms in at_ms:
        jobs.add_checkpoint(ms, Path(f"t{ms}.pt"))
    return jobs


def finish(jobs: GhostJobs) -> Job | None:
    job = jobs.next()
    if job is not None:
        jobs.mark_done(job[0], job[1])
    return job


def test_the_control_runs_in_time_order_one_job_at_a_time() -> None:
    jobs = jobs_with(0, 1000, 2000)
    first = jobs.next()
    assert first == (CONTROL, 0, "t0.pt")
    assert jobs.next() is None  # one at a time
    jobs.mark_done(CONTROL, 0)
    assert [finish(jobs) for _ in range(3)] == [
        (CONTROL, 1000, "t1000.pt"),
        (CONTROL, 2000, "t2000.pt"),
        None,
    ]
    assert jobs.remaining(CONTROL) == 0


def test_the_latest_choice_goes_first_from_the_viewers_playhead() -> None:
    jobs = jobs_with(0, 1000, 2000, 3000)
    jobs.choose("voltage-0.1", from_ms=2500)  # watching second 2
    order = [finish(jobs) for _ in range(8)]
    assert [(k, ms) for k, ms, _ in order] == [  # type: ignore[misc]
        ("voltage-0.1", 2000),
        ("voltage-0.1", 3000),
        ("voltage-0.1", 0),  # then wraps round
        ("voltage-0.1", 1000),
        (CONTROL, 0),
        (CONTROL, 1000),
        (CONTROL, 2000),
        (CONTROL, 3000),
    ]
    jobs.choose(CONTROL, 0)
    assert jobs.next() is None and jobs.remaining("voltage-0.1") == 0


# --- The workers, on the small network ---


@pytest.fixture
def projected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """300 ms of the small timeline, checkpointed every 100 ms."""
    monkeypatch.setattr(workers, "CHECKPOINT_EVERY_MS", 100)
    scenario = timeline_small()
    out: queue.Queue[tuple[Any, ...]] = queue.Queue()

    def parts() -> workers.Parts:
        return scenario.connectome, scenario.senses, scenario.decoder

    run_projector(out, tmp_path, PROBE_ARENA, seed=3, duration_ms=300, parts=parts)
    messages = list(out.queue)
    live = {row[0]: row for m in messages if m[0] == "chunk" for row in m[2]}
    checkpoints = {m[1]: m[2] for m in messages if m[0] == "checkpoint"}
    return {"dir": tmp_path, "parts": parts, "live": live, "checkpoints": checkpoints}


def ghosts(projected: dict[str, Any], jobs: list[tuple[str, int, str]]) -> list[tuple[Any, ...]]:
    inbox: queue.Queue[tuple[str, int, str] | None] = queue.Queue()
    for job in [*jobs, None]:
        inbox.put(job)
    out: queue.Queue[tuple[Any, ...]] = queue.Queue()
    run_ghost(inbox, out, PROBE_ARENA, horizon_ms=100, parts=projected["parts"])
    return list(out.queue)


def test_projector_reports_spikes_in_transit_at_each_checkpoint(projected: dict[str, Any]) -> None:
    assert sorted(projected["checkpoints"]) == [0, 100, 200]
    scenario = timeline_small()
    for at_ms, in_flight in projected["checkpoints"].items():
        saved = scenario.load(checkpoint_path(projected["dir"], at_ms))
        assert in_flight == int(saved.brain.state.in_flight.sum())


def test_the_control_ghost_matches_live_bit_for_bit_and_keeps_its_checkpoint(
    projected: dict[str, Any],
) -> None:
    path = str(checkpoint_path(projected["dir"], 100))
    (kind, knowledge, from_ms, poses), done = ghosts(projected, [(CONTROL, 100, path)])
    assert (kind, knowledge, from_ms, done) == ("ghost", CONTROL, 100, ("ghost_done",))
    assert [tuple(p) for p in poses] == [projected["live"][t] for t in range(101, 201)]
    assert Path(path).exists()  # kept for other settings at the same moment


@pytest.mark.parametrize("setting", SETTINGS[1:], ids=[s.id for s in SETTINGS[1:]])
def test_an_imperfect_ghost_starts_from_the_blurred_live_state(
    projected: dict[str, Any], setting: Setting
) -> None:
    assert projected["checkpoints"][100] > 0  # a spike in transit, so every setting applies
    path = checkpoint_path(projected["dir"], 100)
    (kind, knowledge, _, poses), _ = ghosts(projected, [(setting.id, 100, str(path))])
    assert (kind, knowledge) == ("ghost", setting.id)
    # The same blur, applied by hand, gives the same ghost: the worker adds nothing else.
    # (On this small network the path often survives the error: a brain difference need
    # not become a behaviour difference, so no peel is demanded here.)
    by_hand = timeline_small().load(path)
    assert setting.knowledge is not None
    blur(by_hand.brain.state, setting.knowledge)
    assert poses == [workers.pose_row(p) for p in by_hand.run(100)]


def test_a_missed_spike_is_refused_exactly_when_nothing_is_in_transit(
    projected: dict[str, Any],
) -> None:
    moments = sorted(projected["checkpoints"])
    answers = ghosts(
        projected,
        [("drop-spike", ms, str(checkpoint_path(projected["dir"], ms))) for ms in moments],
    )[:-1]
    assert projected["checkpoints"][0] == 0  # the first moment: nothing has fired yet
    for ms, answer in zip(moments, answers, strict=True):
        assert answer[1:3] == ("drop-spike", ms)
        quiet = projected["checkpoints"][ms] == 0
        assert answer[0] == ("refused" if quiet else "ghost")
        if quiet:
            assert "no spike in transit" in answer[3]


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
    return server.Run(settings=server.Settings(), hello=None)  # type: ignore[arg-type]


def touch_checkpoint(run: server.Run, at_ms: int) -> None:
    run.settings.checkpoints.mkdir(parents=True, exist_ok=True)
    checkpoint_path(run.settings.checkpoints, at_ms).touch()


def test_a_chosen_setting_is_computed_and_cached_under_its_own_key(run: server.Run) -> None:
    fake = FakeWorkers()
    outbox: Any = queue.Queue()
    run.outboxes.add(outbox)  # type: ignore[arg-type]
    touch_checkpoint(run, 0)
    run.accept(("checkpoint", 0, 5), fake)
    assert fake.sent[-1][:2] == (CONTROL, 0)
    run.choose(Choose(knowledge="voltage-0.01", from_ms=0), fake)
    assert len(fake.sent) == 1  # the ghost is busy: nothing more is sent
    run.accept(("chunk", 0, rows(1, 101), np.array([1]), 1), fake)
    run.accept(("ghost", CONTROL, 0, rows(1, 101)), fake)
    assert fake.sent[-1][:2] == ("voltage-0.01", 0)
    run.accept(("projector_done",), fake)
    assert server.cache_path(run.settings).exists()  # the control is complete
    run.accept(("ghost", "voltage-0.01", 0, rows(1, 51) + rows(51, 101, x0=1.0)), fake)
    cached = server.cache_path(run.settings, BY_ID["voltage-0.01"])
    assert cached.exists() and BY_ID["voltage-0.01"].key in cached.name
    sent = [json.loads(outbox.get_nowait()) for _ in range(outbox.qsize())]
    ghost = [m for m in sent if m["type"] == "ghost" and m["knowledge"] == "voltage-0.01"]
    assert len(ghost) == 1
    final = [m for m in sent if m["type"] == "match" and m["knowledge"] == "voltage-0.01"][-1]
    assert (final["compared_ms"], final["close_ms"], final["right_for"]) == (100, 50, [[0, 50]])

    # A restart replays both settings from disk, with nothing to compute.
    again = server.Run(settings=run.settings, hello=None)  # type: ignore[arg-type]
    assert server.load_cache(again)
    assert again.history.match("voltage-0.01").right_for == [(0, 50)]
    assert again.history.checkpoints[0].in_flight == 5
    assert again.jobs.remaining("voltage-0.01") == 0 and not again.computing


def test_a_refusal_is_recorded_and_cached_never_replaced_by_a_copy(run: server.Run) -> None:
    fake = FakeWorkers()
    touch_checkpoint(run, 0)
    run.accept(("checkpoint", 0, 0), fake)
    run.accept(("ghost", CONTROL, 0, rows(1, 101)), fake)
    run.accept(("projector_done",), fake)
    run.choose(Choose(knowledge="drop-spike"), fake)
    run.accept(("refused", "drop-spike", 0, "no spike in transit to miss at this moment"), fake)
    track = run.history.track("drop-spike")
    assert track.ghosts == [] and 0 in track.refused
    saved = json.loads(server.cache_path(run.settings, BY_ID["drop-spike"]).read_text())
    assert saved == {"ghosts": [], "refused": [[0, "no spike in transit to miss at this moment"]]}


def test_a_missing_checkpoint_is_refused_not_sent(run: server.Run) -> None:
    fake = FakeWorkers()
    run.accept(("checkpoint", 0, 3), fake)  # no file behind it
    assert fake.sent == []
    assert "missing" in run.history.track(CONTROL).refused[0].reason


def test_status_says_how_many_ghosts_each_choice_still_needs(run: server.Run) -> None:
    fake = FakeWorkers()
    for ms in (0, 1000):
        touch_checkpoint(run, ms)
        run.accept(("checkpoint", ms, 1), fake)
    run.choose(Choose(knowledge="float32", from_ms=0), fake)
    assert run.status().to_compute == {CONTROL: 2, "float32": 2}


@pytest.mark.skipif(not (DATA_DIR / ANNOTATIONS_FILE).exists(), reason="needs fetch_data.py")
def test_a_viewer_can_choose_over_the_websocket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TRAMLINES_ARENA", "default")
    monkeypatch.setenv("TRAMLINES_SECONDS", "0.1")
    monkeypatch.setenv("TRAMLINES_HORIZON_MS", "100")
    monkeypatch.setattr(server, "PROJECTIONS", tmp_path)
    cached = {
        "chunks": [chunk(0, 100).model_dump()],
        "checkpoints": [[0, 2]],
        "ghosts": [[0, rows(1, 101)]],
    }
    (tmp_path / f"{server.Settings().key}.json").write_text(json.dumps(cached))
    with TestClient(server.app) as client, client.websocket_connect("/stream") as ws:
        for _ in range(6):  # hello, chunk, checkpoint, ghost, match, status
            ws.receive_text()
        ws.send_text("not json")  # ignored
        ws.send_text(json.dumps({"type": "choose", "knowledge": "voltage-0.1", "from_ms": 0}))
        # Its saved moment was deleted, so the server says so instead of computing.
        reply = json.loads(ws.receive_text())
    assert (reply["type"], reply["knowledge"], reply["from_ms"]) == ("refused", "voltage-0.1", 0)
    assert "missing" in reply["reason"]
