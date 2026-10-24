"""What the server remembers about a run, and the ghost-versus-live comparison (ADR-0033).

Pure bookkeeping, no processes or sockets, so it can be tested directly. Each
knowledge setting has its own track of ghosts and scores (ADR-0042); the live
timeline is shared by all of them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from tramlines.server.knowledge import CONTROL, RIGHT_WITHIN_MM
from tramlines.server.protocol import Checkpoint, Chunk, Ghost, Match, PoseRow, Refused


@dataclass
class Track:
    """The ghosts of one knowledge setting, and how they compared with the live fly."""

    knowledge: str
    ghosts: list[Ghost] = field(default_factory=list)
    full: dict[int, list[PoseRow]] = field(default_factory=dict)  # from_ms -> every pose
    refused: dict[int, Refused] = field(default_factory=dict)  # from_ms -> why not made
    compared_ms: int = 0
    matched_ms: int = 0  # bit for bit
    close_ms: int = 0  # within RIGHT_WITHIN_MM
    # Per simulated second: [compared, matched, close], so a viewer can count only what it
    # has played (issue #14, B7).
    by_second: dict[int, list[int]] = field(default_factory=dict)
    right_for: dict[int, int] = field(default_factory=dict)  # from_ms -> ms on path, once known
    _unscored: list[tuple[int, PoseRow]] = field(default_factory=list)  # (from_ms, pose)
    _left: dict[int, int] = field(default_factory=dict)  # from_ms -> poses not yet scored
    _first_off: dict[int, int] = field(default_factory=dict)  # from_ms -> first ms off path

    def done(self) -> set[int]:
        """Checkpoints this setting has answered, with a ghost or a refusal."""
        return set(self.full) | set(self.refused)

    def add(self, from_ms: int, poses: list[PoseRow]) -> Ghost | None:
        """Keep the full path for scoring; return the thinned copy, or None if already known."""
        if from_ms in self.full:
            return None
        self.full[from_ms] = poses
        self._left[from_ms] = len(poses)
        self._unscored.extend((from_ms, row) for row in poses)
        ghost = Ghost(knowledge=self.knowledge, from_ms=from_ms, poses=poses[9::10])
        self.ghosts.append(ghost)
        return ghost

    def score(self, live: dict[int, PoseRow]) -> None:
        """Compare each ghost pose with the live pose at the same millisecond, once."""
        waiting = []
        for from_ms, row in self._unscored:
            truth = live.get(row[0])
            if truth is None:
                waiting.append((from_ms, row))
                continue
            same = int(row == truth)  # every field, exactly
            close = int(math.hypot(row[1] - truth[1], row[2] - truth[2]) <= RIGHT_WITHIN_MM)
            self.compared_ms += 1
            self.matched_ms += same
            self.close_ms += close
            counts = self.by_second.setdefault((row[0] - 1) // 1000, [0, 0, 0])
            counts[0] += 1
            counts[1] += same
            counts[2] += close
            if not close:
                self._first_off[from_ms] = min(self._first_off.get(from_ms, row[0]), row[0])
            self._left[from_ms] -= 1
            if not self._left[from_ms]:
                # Same convention as Result 1: ms on path before the first pose off it.
                first_off = self._first_off.get(from_ms)
                horizon = len(self.full[from_ms])
                self.right_for[from_ms] = horizon if first_off is None else first_off - from_ms - 1
        self._unscored = waiting

    def match(self) -> Match:
        return Match(
            knowledge=self.knowledge,
            compared_ms=self.compared_ms,
            matched_ms=self.matched_ms,
            close_ms=self.close_ms,
            by_second=[(s, c, m, n) for s, (c, m, n) in sorted(self.by_second.items())],
            right_for=sorted(self.right_for.items()),
        )


@dataclass
class RunHistory:
    chunks: list[Chunk] = field(default_factory=list)
    checkpoints: dict[int, Checkpoint] = field(default_factory=dict)  # at_ms -> checkpoint
    live: dict[int, PoseRow] = field(default_factory=dict)  # time_ms -> pose
    # Knowledge setting -> its ghosts; the control's track is always there.
    tracks: dict[str, Track] = field(default_factory=lambda: {CONTROL: Track(CONTROL)})
    frontier_ms: int = 0  # the live timeline is computed up to here

    def track(self, knowledge: str = CONTROL) -> Track:
        return self.tracks.setdefault(knowledge, Track(knowledge))

    def add_chunk(self, chunk: Chunk) -> None:
        self.chunks.append(chunk)
        for row in chunk.poses:
            self.live[row[0]] = row
            self.frontier_ms = max(self.frontier_ms, row[0])
        for track in self.tracks.values():
            track.score(self.live)

    def add_checkpoint(self, checkpoint: Checkpoint) -> None:
        self.checkpoints[checkpoint.at_ms] = checkpoint

    def add_ghost(
        self, from_ms: int, poses: list[PoseRow], knowledge: str = CONTROL
    ) -> Ghost | None:
        """Keep a ghost's full path for scoring; return the thinned copy for the viewer."""
        track = self.track(knowledge)
        ghost = track.add(from_ms, poses)
        track.score(self.live)
        return ghost

    def refuse(self, from_ms: int, knowledge: str, reason: str) -> Refused:
        refused = Refused(knowledge=knowledge, from_ms=from_ms, reason=reason)
        self.track(knowledge).refused[from_ms] = refused
        return refused

    def match(self, knowledge: str = CONTROL) -> Match:
        return self.track(knowledge).match()
