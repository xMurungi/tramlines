"""Compute every knowledge setting for the demo run ahead of time (owner decision 25).

The viewer computes a setting when someone first chooses it, about 35 minutes for a
60 s run, then caches it (ADR-0042). For the demo, every setting is computed once in
advance so the slider answers at once (and a precomputed run is what Phase 7 ships,
owner decision 19).

Run it only once the code is frozen for the demo: a cached run is keyed by all of the
package's code (issue #14, B2), so any later code change throws the hours away.

    uv run python -m tramlines.server.precompute     # the server's TRAMLINES_* settings
"""

from __future__ import annotations

import queue
import time
from collections.abc import Callable
from typing import Any, Protocol

from tramlines.server.app import (
    Run,
    Settings,
    WorkerPool,
    Workers,
    load_cache,
    neuron_xy,
)
from tramlines.server.knowledge import CONTROL, SETTINGS
from tramlines.server.protocol import Choose, Hello
from tramlines.server.workers import ARENAS

REPORT_EVERY_S = 60.0


class Pool(WorkerPool, Protocol):
    out: Any


def choose_all(run: Run, workers: WorkerPool) -> None:
    """Every setting, the control first (the latest choice goes first, ADR-0042)."""
    for setting in reversed(SETTINGS):
        run.choose(Choose(knowledge=setting.id, from_ms=0), workers)


def finished(run: Run) -> bool:
    return all(s.id in run.saved for s in SETTINGS)


def remaining(run: Run) -> str:
    return ", ".join(
        f"{s.id} {run.jobs.remaining(s.id)}" for s in SETTINGS if s.id not in run.saved
    )


def drain(
    run: Run,
    workers: Pool,
    poll_s: float = 0.5,
    report: Callable[[str], None] = print,
    report_every_s: float = REPORT_EVERY_S,
) -> None:
    """Feed worker messages to the run until every setting is cached."""
    last = time.monotonic()
    while not finished(run):
        try:
            message = workers.out.get(True, poll_s)
        except queue.Empty:
            if dead := workers.dead():
                raise RuntimeError(f"{', '.join(dead)} stopped unexpectedly") from None
            continue
        run.accept(message, workers)
        if time.monotonic() - last >= report_every_s:
            report(f"ghosts still to compute: {remaining(run) or 'none'}")
            last = time.monotonic()


def main() -> None:
    settings = Settings()
    arena = ARENAS[settings.arena]
    hello = Hello.describe(
        settings.arena, arena, settings.seed, settings.horizon_ms, settings.duration_ms, neuron_xy()
    )
    run = Run(settings=settings, hello=hello)
    workers = Workers(settings)
    try:
        if not load_cache(run):
            print("no cached live run: computing it first")
            workers.start_projector()
        if finished(run):
            print("every setting is already cached")
            return
        choose_all(run, workers)
        print(f"computing: {remaining(run)} (the control is {CONTROL!r})", flush=True)
        drain(run, workers)
        print("done: every setting is cached")
    finally:
        workers.stop()


if __name__ == "__main__":
    main()
