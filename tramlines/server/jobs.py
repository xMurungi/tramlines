"""Which ghost the ghost process computes next (ADR-0042).

One ghost process serves every knowledge setting, one job at a time, so the
server never runs more than two brain processes (ADR-0032). Pure bookkeeping,
tested directly.

Order: a free-will fan comes first, the most recently asked first (ADR-0046): it is
the one thing a viewer has just pressed a button for. Then the setting a viewer chose
most recently, starting at the checkpoint behind that viewer's playhead and going
forward, then wrapping round to earlier moments. The control is chosen at the start,
so with no other choice it runs in time order, as in ADR-0033.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from tramlines.server.fans import FAN
from tramlines.server.knowledge import CONTROL

# (knowledge setting, checkpoint ms, saved state file), or for a fan
# (FAN, the moment the spikes are added, the saved state file behind it).
Job = tuple[str, int, str]


@dataclass
class GhostJobs:
    checkpoints: dict[int, Path] = field(default_factory=dict)  # at_ms -> saved state
    # Chosen settings -> the playhead they were chosen at; the latest choice is last.
    chosen: dict[str, int] = field(default_factory=lambda: {CONTROL: 0})
    done: set[tuple[str, int]] = field(default_factory=set)
    running: tuple[str, int] | None = None
    # Fans asked for -> the saved state behind them; the latest request is last.
    fans: dict[int, Path] = field(default_factory=dict)

    def add_checkpoint(self, at_ms: int, path: Path) -> None:
        self.checkpoints[at_ms] = path

    def choose(self, knowledge: str, from_ms: int) -> None:
        self.chosen.pop(knowledge, None)
        self.chosen[knowledge] = from_ms

    def want_fan(self, at_ms: int, path: Path) -> None:
        self.fans.pop(at_ms, None)
        self.fans[at_ms] = path

    def fans_remaining(self) -> int:
        return sum((FAN, ms) not in self.done for ms in self.fans)

    def mark_done(self, knowledge: str, at_ms: int) -> None:
        self.done.add((knowledge, at_ms))
        if self.running == (knowledge, at_ms):
            self.running = None

    def remaining(self, knowledge: str) -> int:
        return sum((knowledge, ms) not in self.done for ms in self.checkpoints)

    def next(self) -> Job | None:
        """The next job to send, or None while one is running or nothing is left."""
        if self.running is not None:
            return None
        for at_ms in reversed(self.fans):
            if (FAN, at_ms) not in self.done:
                self.running = (FAN, at_ms)
                return FAN, at_ms, str(self.fans[at_ms])
        for knowledge, from_ms in reversed(self.chosen.items()):
            pending = sorted(ms for ms in self.checkpoints if (knowledge, ms) not in self.done)
            if not pending:
                continue
            behind = max((ms for ms in self.checkpoints if ms <= from_ms), default=0)
            at_ms = next((ms for ms in pending if ms >= behind), pending[0])
            self.running = (knowledge, at_ms)
            return knowledge, at_ms, str(self.checkpoints[at_ms])
        return None
