"""What the server remembers about a run, and the ghost-versus-live comparison (ADR-0033).

Pure bookkeeping, no processes or sockets, so it can be tested directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tramlines.server.protocol import Chunk, Ghost, Match, PoseRow


@dataclass
class RunHistory:
    chunks: list[Chunk] = field(default_factory=list)
    ghosts: list[Ghost] = field(default_factory=list)
    live: dict[int, PoseRow] = field(default_factory=dict)  # time_ms -> pose
    ghost_full: dict[int, list[PoseRow]] = field(default_factory=dict)  # from_ms -> every pose
    compared_ms: int = 0
    matched_ms: int = 0
    frontier_ms: int = 0  # the live timeline is computed up to here
    # Per simulated second: [compared, matched], so a viewer can count only what it has
    # played (issue #14, B7).
    by_second: dict[int, list[int]] = field(default_factory=dict)
    _unscored: list[PoseRow] = field(default_factory=list)  # ghost poses not yet comparable

    def add_chunk(self, chunk: Chunk) -> None:
        self.chunks.append(chunk)
        for row in chunk.poses:
            self.live[row[0]] = row
            self.frontier_ms = max(self.frontier_ms, row[0])
        self._score()

    def add_ghost(self, from_ms: int, poses: list[PoseRow]) -> Ghost:
        """Keep the ghost's full path for scoring; return the thinned copy for the viewer."""
        self.ghost_full[from_ms] = poses
        self._unscored.extend(poses)
        ghost = Ghost(from_ms=from_ms, poses=poses[9::10])
        self.ghosts.append(ghost)
        self._score()
        return ghost

    def match(self) -> Match:
        return Match(
            compared_ms=self.compared_ms,
            matched_ms=self.matched_ms,
            by_second=[(s, c, m) for s, (c, m) in sorted(self.by_second.items())],
        )

    def _score(self) -> None:
        """Compare each ghost pose with the live pose at the same millisecond, once."""
        waiting = []
        for row in self._unscored:
            live = self.live.get(row[0])
            if live is None:
                waiting.append(row)
                continue
            same = int(row == live)  # every field, exactly
            self.compared_ms += 1
            self.matched_ms += same
            counts = self.by_second.setdefault((row[0] - 1) // 1000, [0, 0])
            counts[0] += 1
            counts[1] += same
        self._unscored = waiting
