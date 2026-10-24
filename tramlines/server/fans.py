"""What the server remembers about free-will fans, and when free will is offered (ADR-0046).

Pure bookkeeping, no processes or sockets, so it can be tested directly. The fans
themselves are computed by the ghost process (`tramlines.server.workers`) with
`tramlines.timeline.branches`; this module keeps their results, checks each fan's
untouched future against the live fly, and names its cache file.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from tramlines.server.protocol import Decisions, Fan, FanBranch, PoseRow
from tramlines.timeline.branches import APART_MM, BRAIN_SAME_WITHIN_MV, SPIKE_BIN_MS
from tramlines.world.arena import Arena

FAN = "fan"  # a fan job in the ghost's queue; never a knowledge setting's id
BRANCHES = 8  # owner decision 9
# The aim (ADR-0031): driven input neurons, tried in an order drawn from a generator
# seeded by the moment in ms, so the same moment always gets the same spikes.
AIM_RULE = "driven inputs; torch.randperm seeded by at_ms; refused spikes replaced"


def fan_key() -> str:
    """Part of a fan's cache key: everything about a fan that is not already in the run key
    (which fingerprints the code, the model's numbers, the data, the seed and the horizon)."""
    rule = repr((BRANCHES, AIM_RULE, APART_MM, BRAIN_SAME_WITHIN_MV, SPIKE_BIN_MS))
    return hashlib.sha256(rule.encode()).hexdigest()[:8]


def decision_at(row: PoseRow, arena: Arena) -> str | None:
    """What the world is asking the brain at this pose, or None while the fly only walks.

    These are the moments when a sense other than the walking drive receives input,
    so an aimed spike has more than the walking drive to land in (ADR-0031, ADR-0032).
    """
    time_ms, x_mm, y_mm = row[0], row[1], row[2]
    if arena.active_loom(time_ms) is not None:
        return "a shadow approaching"
    kinds = {p.kind for p in arena.patches_under(x_mm, y_mm) if p.strength > 0}
    if kinds == {"food", "bitter"}:
        return "on laced food"
    if kinds:
        return f"on {kinds.pop()}"
    return None


@dataclass
class DecisionLog:
    """Decision moments of the live timeline, as runs of consecutive milliseconds."""

    arena: Arena
    moments: list[tuple[int, int, str]] = field(default_factory=list)
    _seen_ms: int = 0  # poses up to here have been read

    def add(self, poses: list[PoseRow]) -> bool:
        """Read new live poses (in time order); True if the moments changed."""
        changed = False
        for row in poses:
            if row[0] <= self._seen_ms:
                continue
            self._seen_ms = row[0]
            what = decision_at(row, self.arena)
            if what is None:
                continue
            last = self.moments[-1] if self.moments else None
            if last is not None and last[1] == row[0] - 1 and last[2] == what:
                self.moments[-1] = (last[0], row[0], what)
            else:
                self.moments.append((row[0], row[0], what))
            changed = True
        return changed

    def at(self, time_ms: int) -> str | None:
        return next((what for a, b, what in self.moments if a <= time_ms <= b), None)

    def message(self) -> Decisions:
        return Decisions(moments=list(self.moments))


@dataclass
class FanRecord:
    fan: Fan
    branches: dict[int, FanBranch] = field(default_factory=dict)  # index -> branch
    base_full: list[PoseRow] = field(default_factory=list)  # every pose of the untouched future

    def set_base(self, poses: list[PoseRow]) -> None:
        self.base_full = poses
        self.fan.base = poses[9::10]

    def score(self, live: dict[int, PoseRow]) -> bool:
        """Compare the untouched future with the live fly, bit for bit; True if it changed."""
        known = [row for row in self.base_full if row[0] in live]
        compared = len(known)
        if compared == self.fan.base_compared_ms:
            return False
        self.fan.base_compared_ms = compared
        self.fan.base_matched_ms = sum(row == live[row[0]] for row in known)
        return True

    def messages(self) -> list[Fan | FanBranch]:
        return [self.fan, *(self.branches[i] for i in sorted(self.branches))]


@dataclass
class FanHistory:
    records: dict[int, FanRecord] = field(default_factory=dict)  # at_ms -> fan

    def get(self, at_ms: int) -> FanRecord | None:
        return self.records.get(at_ms)

    def add(self, fan: Fan) -> FanRecord:
        record = self.records.setdefault(fan.at_ms, FanRecord(fan))
        return record

    def score(self, live: dict[int, PoseRow]) -> list[Fan]:
        """Re-check every fan against the live fly; return the fans whose check changed."""
        return [r.fan for r in self.records.values() if r.score(live)]
