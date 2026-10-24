"""How much the ghost knows: the stops of the viewer's knowledge slider (ADR-0042).

The perfect ghost is a bit-exact copy and is always right, because the simulation
is deterministic: it is the control, not a prediction (ADR-0035). The other stops
come from Result 1 (ADR-0037, ADR-0038): each starts the ghost from the live brain
blurred by `tramlines.timeline.perturb.blur`, the way a real measurement could fall
short. The body and the arena are known exactly; only the brain is measured.

The order is by kind of error, and within a kind by its size: continuous error
(float32 rounding is about 10⁻⁶ mV, smaller than any voltage stop), then partial
observation, then one missed spike. Kinds are not ranked against each other.
"""

from __future__ import annotations

import csv
import functools
import hashlib
from dataclasses import dataclass
from pathlib import Path

from tramlines.timeline.perturb import Knowledge

CONTROL = "control"
# "Right" means the ghost's path is within this distance of the live fly's, as in
# Result 1 (scripts/horizon_study.py, EPSILON_MM; ADR-0037).
RIGHT_WITHIN_MM = 0.1
# Result 1's second pass (ADR-0038): how often each error kept the ghost right, shown
# beside the slider, because the ghost on screen is one draw (owner decision 24).
RESULT1_CSV = Path(__file__).resolve().parents[2] / "docs" / "assets" / "horizon_v2.csv"
RESULT1_HORIZON_MS = 3_000
RESULT1_MOMENTS = ("walking", "laced food", "shadow")


@dataclass(frozen=True)
class Evidence:
    """In Result 1, at one moment of the decision dish: ghosts right for all 3 s, of all made."""

    moment: str
    right: int
    total: int


@dataclass(frozen=True)
class Setting:
    id: str
    label: str  # the slider stop, a few characters
    knowledge: Knowledge | None  # None: the control, a bit-exact copy

    @property
    def description(self) -> str:
        if self.knowledge is None:
            return "everything: a bit-exact copy (the control)"
        return self.knowledge.describe()

    @property
    def needs_spike_in_transit(self) -> bool:
        """Only offered at moments with a spike travelling; `blur` refuses otherwise."""
        return self.knowledge is not None and self.knowledge.kind == "drop_spike"

    @property
    def evidence(self) -> tuple[Evidence, ...]:
        """Result 1's counts for this error, one per moment (empty if the data is absent)."""
        label = "everything (control)" if self.knowledge is None else self.knowledge.describe()
        rows = [r for r in _result1_rows() if r["ghost_knows"] == label]
        out = []
        for moment in RESULT1_MOMENTS:
            mine = [r for r in rows if r["moment"] == moment]
            if mine:
                right = sum(int(r["path_stays_right_ms"]) >= RESULT1_HORIZON_MS for r in mine)
                out.append(Evidence(moment, right, len(mine)))
        return tuple(out)

    @property
    def key(self) -> str:
        """Part of the cache key: changes with the error's kind, size or random draw."""
        digest = hashlib.sha256(repr(self.knowledge).encode()).hexdigest()[:8]
        return f"{self.id}-{digest}"


# Draw 0 of every random error (seed 0), the draw the first pass used (ADR-0037).
SETTINGS: tuple[Setting, ...] = (
    Setting(CONTROL, "everything", None),
    Setting("float32", "float32", Knowledge("float32")),
    Setting("voltage-0.001", "0.001 mV", Knowledge("voltage", 1e-3)),
    Setting("voltage-0.01", "0.01 mV", Knowledge("voltage", 1e-2)),
    Setting("voltage-0.1", "0.1 mV", Knowledge("voltage", 1e-1)),
    Setting("partial-0.999", "99.9% seen", Knowledge("partial", 0.999)),
    Setting("partial-0.99", "99% seen", Knowledge("partial", 0.99)),
    Setting("drop-spike", "1 spike missed", Knowledge("drop_spike")),
)
BY_ID: dict[str, Setting] = {s.id: s for s in SETTINGS}


@functools.cache
def _result1_rows() -> tuple[dict[str, str], ...]:
    if not RESULT1_CSV.exists():
        return ()
    with RESULT1_CSV.open() as f:
        return tuple(csv.DictReader(f))
