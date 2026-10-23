"""The Tramlines server: FastAPI + one WebSocket (ADR-0005, ADR-0033).

    uv run python -m tramlines.server            # then open http://127.0.0.1:8000

Settings (environment): TRAMLINES_ARENA (decision | default), TRAMLINES_SEED (0),
TRAMLINES_SECONDS (60, the Phase 4 gate), TRAMLINES_HORIZON_MS (3000). A finished run is cached in
`data/projections/` and replayed instantly next time; delete the file to recompute.
"""

from __future__ import annotations

import asyncio
import json
import multiprocessing as mp
import os
import queue
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from tramlines.brain.data import COMPLETENESS_FILE, DATA_DIR
from tramlines.brain.neurons import ANNOTATIONS_FILE
from tramlines.server.history import RunHistory
from tramlines.server.protocol import Chunk, Ghost, Hello, Status, encode_indices
from tramlines.server.workers import ARENAS, run_ghost, run_projector

ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = ROOT / "web" / "dist"
PROJECTIONS = DATA_DIR / "projections"


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
        return f"{self.arena}_seed{self.seed}_{self.duration_ms}ms_h{self.horizon_ms}"


@dataclass
class Run:
    settings: Settings
    hello: Hello
    history: RunHistory = field(default_factory=RunHistory)
    ghost_checkpoint_ms: int | None = None
    computing: bool = True
    cached: bool = False
    clients: set[WebSocket] = field(default_factory=set)

    def status(self) -> Status:
        return Status(
            frontier_ms=self.history.frontier_ms,
            ghost_checkpoint_ms=self.ghost_checkpoint_ms,
            computing=self.computing,
            cached=self.cached,
        )

    async def broadcast(self, *messages: BaseModel) -> None:
        for ws in list(self.clients):
            try:
                for message in messages:
                    await ws.send_text(message.model_dump_json())
            except (WebSocketDisconnect, RuntimeError):
                self.clients.discard(ws)


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


def cache_path(settings: Settings) -> Path:
    return PROJECTIONS / f"{settings.key}.json"


def load_cache(run: Run) -> bool:
    path = cache_path(run.settings)
    if not path.exists():
        return False
    saved = json.loads(path.read_text())
    for chunk in saved["chunks"]:
        run.history.add_chunk(Chunk(**chunk))
    for from_ms, poses in saved["ghosts"]:
        run.history.add_ghost(from_ms, [tuple(p) for p in poses])
        run.ghost_checkpoint_ms = from_ms
    run.computing, run.cached = False, True
    return True


def save_cache(run: Run) -> None:
    PROJECTIONS.mkdir(parents=True, exist_ok=True)
    saved = {
        "chunks": [c.model_dump() for c in run.history.chunks],
        "ghosts": [[k, v] for k, v in run.history.ghost_full.items()],
    }
    cache_path(run.settings).write_text(json.dumps(saved))


async def pump(run: Run, out: Any, ghost_inbox: Any) -> None:
    """Relay worker messages to the history and every connected viewer."""
    while True:
        try:
            message = await asyncio.to_thread(out.get, True, 0.5)
        except queue.Empty:
            continue
        kind = message[0]
        if kind == "chunk":
            _, t0_ms, poses, fired, spikes = message
            chunk = Chunk(t0_ms=t0_ms, poses=poses, fired=encode_indices(fired), spikes=spikes)
            run.history.add_chunk(chunk)
            await run.broadcast(chunk, run.history.match(), run.status())
        elif kind == "checkpoint":
            ghost_inbox.put((message[1], message[2]))
        elif kind == "ghost":
            _, from_ms, poses = message
            ghost: Ghost = run.history.add_ghost(from_ms, poses)
            run.ghost_checkpoint_ms = from_ms
            await run.broadcast(ghost, run.history.match(), run.status())
        elif kind == "projector_done":
            ghost_inbox.put(None)
        elif kind == "ghost_done":
            run.computing = False
            save_cache(run)
            await run.broadcast(run.status())
            return


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    arena = ARENAS[settings.arena]
    hello = Hello.describe(
        settings.arena, arena, settings.seed, settings.horizon_ms, settings.duration_ms, neuron_xy()
    )
    run = Run(settings=settings, hello=hello)
    app.state.run = run
    processes: list[mp.process.BaseProcess] = []
    task = None
    if not load_cache(run):
        context = mp.get_context("spawn")
        out, ghost_inbox = context.Queue(), context.Queue()
        checkpoints = PROJECTIONS / f"{settings.key}_checkpoints"
        processes = [
            context.Process(
                target=run_projector,
                args=(out, checkpoints, settings.arena, settings.seed, settings.duration_ms),
                daemon=True,
            ),
            context.Process(
                target=run_ghost,
                args=(ghost_inbox, out, settings.arena, settings.horizon_ms),
                daemon=True,
            ),
        ]
        for process in processes:
            process.start()
        task = asyncio.create_task(pump(run, out, ghost_inbox))
    yield
    if task:
        task.cancel()
    for process in processes:
        process.terminate()


app = FastAPI(title="Tramlines", lifespan=lifespan)


@app.websocket("/stream")
async def stream(ws: WebSocket) -> None:
    run: Run = ws.app.state.run
    await ws.accept()
    await ws.send_text(run.hello.model_dump_json())
    for message in [*run.history.chunks, *run.history.ghosts]:
        await ws.send_text(message.model_dump_json())
    await ws.send_text(run.history.match().model_dump_json())
    await ws.send_text(run.status().model_dump_json())
    run.clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        run.clients.discard(ws)


if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="viewer")
