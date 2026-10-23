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
    _unscored: list[PoseRow] = field(default_factory=list)  # ghost poses not yet comparable

    @property
    def frontier_ms(self) -> int:
        return max(self.live) if self.live else 0

    def add_chunk(self, chunk: Chunk) -> None:
        self.chunks.append(chunk)
        for row in chunk.poses:
            self.live[row[0]] = row
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
        return Match(compared_ms=self.compared_ms, matched_ms=self.matched_ms)

    def _score(self) -> None:
        """Compare each ghost pose with the live pose at the same millisecond, once."""
        waiting = []
        for row in self._unscored:
            live = self.live.get(row[0])
            if live is None:
                waiting.append(row)
                continue
            self.compared_ms += 1
            self.matched_ms += int(row == live)  # every field, exactly
        self._unscored = waiting
