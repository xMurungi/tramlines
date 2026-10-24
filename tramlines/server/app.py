"""The Tramlines server: FastAPI + one WebSocket (ADR-0005, ADR-0033).

    uv run python -m tramlines.server            # then open http://127.0.0.1:8000

Settings (environment): TRAMLINES_ARENA (decision | default), TRAMLINES_SEED (0),
TRAMLINES_SECONDS (60, the Phase 4 gate), TRAMLINES_HORIZON_MS (3000). A finished run is cached in
`data/projections/` and replayed instantly next time; delete the file to recompute.

A viewer chooses how much the ghost knows (ADR-XXXX). Each setting's ghosts are
computed on demand by the same ghost process from the run's saved checkpoints
(kept in `data/projections/<key>_checkpoints/`, about 6 MB per simulated second
of the full brain) and cached in their own file, keyed by the setting too.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import multiprocessing as mp
import os
import queue
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from multiprocessing.process import BaseProcess
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import pandas as pd
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from tramlines.brain.data import COMPLETENESS_FILE, CONNECTIVITY_FILE, DATA_DIR
from tramlines.brain.neurons import ANNOTATIONS_FILE
from tramlines.brain.params import PARAMS
from tramlines.server.history import RunHistory, Track
from tramlines.server.jobs import GhostJobs, Job
from tramlines.server.knowledge import BY_ID, CONTROL, SETTINGS, Setting
from tramlines.server.protocol import Checkpoint, Choose, Chunk, Hello, Status, encode_indices
from tramlines.server.workers import ARENAS, checkpoint_path, run_ghost, run_projector

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "tramlines"
WEB_DIST = ROOT / "web" / "dist"
PROJECTIONS = DATA_DIR / "projections"


def build_fingerprint() -> str:
    """Everything a cached run depends on: the code, the model's numbers and the data.

    A change to any of them gives a new cache key, so a stale run is never replayed
    (issue #14, B2).
    """
    digest = hashlib.sha256(repr(PARAMS).encode())
    for path in sorted(PACKAGE.rglob("*.py")):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    for name in (COMPLETENESS_FILE, CONNECTIVITY_FILE, ANNOTATIONS_FILE):
        stat = (DATA_DIR / name).stat()
        digest.update(f"{name}:{stat.st_size}".encode())  # files are checksum-verified on fetch
    return digest.hexdigest()[:12]


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass
class Settings:
    """Read from the environment when the server starts (not when this module is imported)."""

    arena: str = field(default_factory=lambda: _env("TRAMLINES_ARENA", "decision"))
    seed: int = field(default_factory=lambda: int(_env("TRAMLINES_SEED", "0")))
    duration_ms: int = field(
        default_factory=lambda: int(float(_env("TRAMLINES_SECONDS", "60")) * 1000)
    )
    horizon_ms: int = field(default_factory=lambda: int(_env("TRAMLINES_HORIZON_MS", "3000")))

    @property
    def key(self) -> str:
        settings = f"{self.arena}_seed{self.seed}_{self.duration_ms}ms_h{self.horizon_ms}"
        return f"{settings}_{build_fingerprint()}"

    @property
    def checkpoints(self) -> Path:
        return PROJECTIONS / f"{self.key}_checkpoints"


class WorkerPool(Protocol):
    """What a run needs from its brain processes (a protocol, so tests can stand in)."""

    out: Any  # worker messages, read with `get(block, timeout)`

    def send(self, job: Job) -> None: ...

    def dead(self) -> list[str]: ...


class Workers:
    """The run's brain processes, each started only when first needed (ADR-0033, ADR-XXXX).

    At most two: the projector (only while the live timeline is computing) and one
    ghost, which serves every knowledge setting one job at a time.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.context = mp.get_context("spawn")
        self.out: Any = self.context.Queue()
        self.processes: list[BaseProcess] = []
        self._ghost_inbox: Any = None

    def _start(self, name: str, target: Any, args: tuple[Any, ...]) -> None:
        process = self.context.Process(target=target, args=args, name=name, daemon=True)
        process.start()
        self.processes.append(process)

    def start_projector(self) -> None:
        s = self.settings
        args = (self.out, s.checkpoints, ARENAS[s.arena], s.seed, s.duration_ms)
        self._start("projector", run_projector, args)

    def send(self, job: Job) -> None:
        if self._ghost_inbox is None:
            self._ghost_inbox = self.context.Queue()
            s = self.settings
            args = (self._ghost_inbox, self.out, ARENAS[s.arena], s.horizon_ms)
            self._start("ghost", run_ghost, args)
        self._ghost_inbox.put(job)

    def dead(self) -> list[str]:
        return [p.name for p in self.processes if p.exitcode not in (None, 0)]

    def stop(self) -> None:
        for process in self.processes:
            process.terminate()


@dataclass
class Run:
    settings: Settings
    hello: Hello
    history: RunHistory = field(default_factory=RunHistory)
    jobs: GhostJobs = field(default_factory=GhostJobs)
    ghost_checkpoint_ms: int | None = None  # the latest moment the control predicted from
    projector_done: bool = False
    cached: bool = False
    error: str | None = None
    saved: set[str] = field(default_factory=set)  # settings whose cache file is written
    # One outbox per connected viewer (issue #14, B1): broadcasting only queues messages,
    # and each viewer's own task sends them, so no message falls between a viewer's
    # history replay and its live updates.
    outboxes: set[asyncio.Queue[str]] = field(default_factory=set)

    @property
    def computing(self) -> bool:
        """The live timeline and its control ghosts are still being computed."""
        if self.error is not None:
            return False
        return not self.projector_done or self.jobs.remaining(CONTROL) > 0

    def status(self) -> Status:
        to_compute = {k: self.jobs.remaining(k) for k in self.jobs.chosen}
        return Status(
            frontier_ms=self.history.frontier_ms,
            ghost_checkpoint_ms=self.ghost_checkpoint_ms,
            computing=self.computing,
            cached=self.cached,
            error=self.error,
            to_compute={k: n for k, n in to_compute.items() if n},
        )

    def snapshot(self) -> list[str]:
        """Everything a newly connected viewer needs, in order."""
        messages: list[BaseModel] = [self.hello, *self.history.chunks]
        messages += self.history.checkpoints.values()
        for track in self.history.tracks.values():
            messages += [*track.ghosts, *track.refused.values(), track.match()]
        messages.append(self.status())
        return [m.model_dump_json() for m in messages]

    def broadcast(self, *messages: BaseModel) -> None:
        texts = [m.model_dump_json() for m in messages]
        for outbox in self.outboxes:
            for text in texts:
                outbox.put_nowait(text)

    def accept(self, message: tuple[Any, ...], workers: WorkerPool) -> None:
        """One message from a worker: record it, tell every viewer, keep the ghost busy."""
        kind = message[0]
        if kind == "chunk":
            _, t0_ms, poses, fired, spikes = message
            chunk = Chunk(t0_ms=t0_ms, poses=poses, fired=encode_indices(fired), spikes=spikes)
            self.history.add_chunk(chunk)
            matches = [t.match() for t in self.history.tracks.values()]
            self.broadcast(chunk, *matches, self.status())
        elif kind == "checkpoint":
            _, at_ms, in_flight = message
            checkpoint = Checkpoint(at_ms=at_ms, in_flight=in_flight)
            self.history.add_checkpoint(checkpoint)
            self.jobs.add_checkpoint(at_ms, checkpoint_path(self.settings.checkpoints, at_ms))
            self.broadcast(checkpoint, self.status())
        elif kind == "ghost":
            _, knowledge, from_ms, poses = message
            self.jobs.mark_done(knowledge, from_ms)
            ghost = self.history.add_ghost(from_ms, poses, knowledge)
            if knowledge == CONTROL:
                self.ghost_checkpoint_ms = from_ms
            news: list[BaseModel] = [ghost] if ghost else []
            self.broadcast(*news, self.history.match(knowledge), self.status())
        elif kind == "refused":
            _, knowledge, from_ms, reason = message
            self.jobs.mark_done(knowledge, from_ms)
            refused = self.history.refuse(from_ms, knowledge, reason)
            self.broadcast(refused, self.history.match(knowledge), self.status())
        elif kind == "projector_done":
            self.projector_done = True
            self.broadcast(self.status())
        self.save_finished()
        self.dispatch(workers)

    def choose(self, choice: Choose, workers: WorkerPool) -> None:
        """A viewer wants this setting: compute its ghosts next, from its playhead on."""
        self.jobs.choose(choice.knowledge, choice.from_ms)
        self.history.track(choice.knowledge)  # so its match is sent even before any ghost
        self.dispatch(workers)
        self.broadcast(self.history.match(choice.knowledge), self.status())

    def dispatch(self, workers: WorkerPool) -> None:
        """Send the ghost process its next job, if it is free and one is waiting."""
        while (job := self.jobs.next()) is not None:
            knowledge, at_ms, path = job
            if Path(path).exists():
                workers.send(job)
                return
            # A cached run whose saved moments were deleted: say so, never fake a ghost.
            self.jobs.mark_done(knowledge, at_ms)
            reason = "this saved moment is missing; delete the cached run to recompute it"
            refused = self.history.refuse(at_ms, knowledge, reason)
            self.broadcast(refused, self.history.match(knowledge), self.status())

    def save_finished(self) -> None:
        """Write each setting's cache once every checkpoint of the finished run is answered."""
        if not self.projector_done or self.error is not None:
            return
        for knowledge in [k for k in self.history.tracks if k not in self.saved]:
            if self.jobs.remaining(knowledge) == 0:
                save_cache(self, BY_ID[knowledge])
                self.saved.add(knowledge)


def neuron_xy() -> np.ndarray:
    """Each neuron's position seen from the front (FlyWire x, y), scaled to 0..65535."""
    root_ids = pd.read_csv(DATA_DIR / COMPLETENESS_FILE, index_col=0).index
    pos = pd.read_csv(
        DATA_DIR / ANNOTATIONS_FILE, sep="\t", usecols=["root_id", "pos_x", "pos_y"]
    ).set_index("root_id")
    xy = pos.reindex(root_ids)[["pos_x", "pos_y"]].to_numpy(dtype=np.float64)
    xy = np.where(np.isnan(xy), np.nanmean(xy, axis=0), xy)
    low, high = xy.min(axis=0), xy.max(axis=0)
    scaled: np.ndarray = np.round((xy - low) / (high - low) * 65535).astype(np.uint16)
    return scaled


def cache_path(settings: Settings, setting: Setting = BY_ID[CONTROL]) -> Path:
    """The live timeline and its control share one file; every other setting has its own,
    keyed by its kind, size and random draw as well as the run (ADR-XXXX)."""
    if setting.id == CONTROL:
        return PROJECTIONS / f"{settings.key}.json"
    return PROJECTIONS / f"{settings.key}_{setting.key}.json"


def _track_to_json(track: Track) -> dict[str, Any]:
    return {
        "ghosts": [[k, v] for k, v in track.full.items()],
        "refused": [[r.from_ms, r.reason] for r in track.refused.values()],
    }


def _track_from_json(run: Run, knowledge: str, saved: dict[str, Any]) -> None:
    for from_ms, poses in saved["ghosts"]:
        run.history.add_ghost(from_ms, [tuple(p) for p in poses], knowledge)
        run.jobs.mark_done(knowledge, from_ms)
        if knowledge == CONTROL:
            run.ghost_checkpoint_ms = from_ms
    for from_ms, reason in saved.get("refused", []):
        run.history.refuse(from_ms, knowledge, reason)
        run.jobs.mark_done(knowledge, from_ms)


def load_cache(run: Run) -> bool:
    """Load the cached live run, then any setting already cached for it."""
    path = cache_path(run.settings)
    if not path.exists():
        return False
    saved = json.loads(path.read_text())
    for chunk in saved["chunks"]:
        run.history.add_chunk(Chunk(**chunk))
    for at_ms, in_flight in saved.get("checkpoints", []):
        run.history.add_checkpoint(Checkpoint(at_ms=at_ms, in_flight=in_flight))
        run.jobs.add_checkpoint(at_ms, checkpoint_path(run.settings.checkpoints, at_ms))
    _track_from_json(run, CONTROL, saved)
    run.saved.add(CONTROL)
    for setting in SETTINGS[1:]:
        other = cache_path(run.settings, setting)
        if other.exists():
            _track_from_json(run, setting.id, json.loads(other.read_text()))
            run.saved.add(setting.id)
    run.projector_done, run.cached = True, True
    return True


def save_cache(run: Run, setting: Setting = BY_ID[CONTROL]) -> None:
    PROJECTIONS.mkdir(parents=True, exist_ok=True)
    saved = _track_to_json(run.history.track(setting.id))
    if setting.id == CONTROL:
        saved["chunks"] = [c.model_dump() for c in run.history.chunks]
        saved["checkpoints"] = [[c.at_ms, c.in_flight] for c in run.history.checkpoints.values()]
    path = cache_path(run.settings, setting)
    partial = path.with_suffix(".json.part")
    partial.write_text(json.dumps(saved))
    os.replace(partial, path)  # a crash mid-write never leaves a broken cache (issue #14, B3)


async def pump(run: Run, workers: WorkerPool) -> None:
    """Relay worker messages to the history and every connected viewer."""
    while True:
        try:
            message = await asyncio.to_thread(workers.out.get, True, 0.5)
        except queue.Empty:
            # A worker that stopped without saying it was done has crashed (issue #14, B4).
            dead = workers.dead()
            if dead:
                run.error = f"{', '.join(dead)} stopped unexpectedly; see the server log"
                run.broadcast(run.status())
                return
            continue
        run.accept(message, workers)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    arena = ARENAS[settings.arena]
    hello = Hello.describe(
        settings.arena, arena, settings.seed, settings.horizon_ms, settings.duration_ms, neuron_xy()
    )
    run = Run(settings=settings, hello=hello)
    workers = Workers(settings)
    app.state.run, app.state.workers = run, workers
    if not load_cache(run):
        workers.start_projector()  # the ghost starts with the first checkpoint
    task = asyncio.create_task(pump(run, workers))
    yield
    task.cancel()
    workers.stop()


app = FastAPI(title="Tramlines", lifespan=lifespan)


@app.websocket("/stream")
async def stream(ws: WebSocket) -> None:
    run: Run = ws.app.state.run
    workers: Workers = ws.app.state.workers
    await ws.accept()
    outbox: asyncio.Queue[str] = asyncio.Queue()
    for text in run.snapshot():  # snapshot and registration with no await between them
        outbox.put_nowait(text)
    run.outboxes.add(outbox)

    async def send() -> None:
        while True:
            await ws.send_text(await outbox.get())

    async def listen() -> None:
        while True:
            text = await ws.receive_text()
            try:
                choice = Choose.model_validate_json(text)
            except ValidationError:
                continue  # a malformed or unknown request changes nothing
            run.choose(choice, workers)

    sender, listener = asyncio.create_task(send()), asyncio.create_task(listen())
    try:
        await asyncio.wait({sender, listener}, return_when=asyncio.FIRST_COMPLETED)
    finally:
        run.outboxes.discard(outbox)
        sender.cancel()
        listener.cancel()


if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="viewer")
