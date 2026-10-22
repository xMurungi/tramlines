"""Brain → body: descending-neuron firing rates become movement (ADR-0028).

Pure and deterministic: the same rates always give the same command. Every gain
and threshold lives here, each with its reason. These numbers are our design,
calibrated from the port survey; they are not measured from flies (honesty page).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch

from tramlines.brain.neurons import NeuronCatalog
from tramlines.world.fly import FlyState, MotorCommand

WINDOW_MS = 50  # rates are averaged over the last 50 ms (CLAUDE.md 8.2)

# Forward speed: P9 near 100 Hz (the walking drive) → about 15 mm/s, a typical
# walking speed for Drosophila (roughly 10-20 mm/s).
FORWARD_MM_S_PER_HZ = 0.15
# Backward walking from MDN, same scale. MDN barely fired in the survey.
BACKWARD_MM_S_PER_HZ = 0.15
SPEED_LIMITS_MM_S = (-10.0, 30.0)
# Turning: DNa02 drives turns towards its own side (Rayshubskiy et al. 2020; to be
# verified against the paper). A 40 Hz left-right difference → 180°/s.
TURN_RAD_S_PER_HZ = math.pi / 40.0
TURN_LIMIT_RAD_S = 2.0 * math.pi
# Escape: Giant Fiber above 50 Hz → take-off. Loom drove it to 100-160 Hz in the
# survey. A real escape is a jump into flight that clears several body lengths; in
# 2D it is shown as a 15 mm hop straight ahead, then the body waits JUMP_COOLDOWN_MS.
GIANT_FIBER_JUMP_HZ = 50.0
JUMP_MM = 15.0
# Feeding: MN9 above 30 Hz on either side starts feeding (stop, extend proboscis);
# once feeding, it continues until MN9 falls below 15 Hz. Without this hysteresis
# MN9 hovering near one threshold made feeding flicker on and off (ADR-0028).
# Sugar on food drove MN9 to 60-85 Hz; bitter suppresses it to ~0.
MN9_FEED_START_HZ = 30.0
MN9_FEED_STOP_HZ = 15.0


@dataclass(frozen=True)
class FlyDecoder:
    """Readouts in a fixed order: P9 (4), DNa02 L, R, MDN (4), GF L, R, MN9 L, R."""

    readout_neurons: torch.Tensor
    window_ms: int = WINDOW_MS

    @classmethod
    def from_catalog(cls, catalog: NeuronCatalog) -> FlyDecoder:
        def find(**match: str) -> list[int]:
            return catalog.find(**match)

        readouts = (
            find(hemibrain_type="DNp09")  # P9, 4 neurons
            + find(hemibrain_type="DNa02", side="left")
            + find(hemibrain_type="DNa02", side="right")
            + find(hemibrain_type="MDN")  # 4 neurons
            + find(hemibrain_type="Giant Fiber", side="left")
            + find(hemibrain_type="Giant Fiber", side="right")
            + find(cell_type="CB0701", side="left")  # MN9
            + find(cell_type="CB0701", side="right")
        )
        if len(readouts) != 14:
            raise ValueError(f"expected 14 readout neurons, found {len(readouts)}")
        return cls(readout_neurons=catalog.index_of(readouts))

    def command(self, rates_hz: torch.Tensor, fly: FlyState) -> MotorCommand:
        r = rates_hz.tolist()
        p9, dna02_left, dna02_right = sum(r[0:4]) / 4, r[4], r[5]
        mdn, gf, mn9 = sum(r[6:10]) / 4, max(r[10], r[11]), max(r[12], r[13])
        if gf > GIANT_FIBER_JUMP_HZ:
            return MotorCommand(forward_mm_s=0.0, jump_mm=JUMP_MM)
        if mn9 > (MN9_FEED_STOP_HZ if fly.feeding else MN9_FEED_START_HZ):
            return MotorCommand(feed=True)
        low, high = SPEED_LIMITS_MM_S
        speed = FORWARD_MM_S_PER_HZ * p9 - BACKWARD_MM_S_PER_HZ * mdn
        turn = TURN_RAD_S_PER_HZ * (dna02_left - dna02_right)
        return MotorCommand(
            forward_mm_s=min(max(speed, low), high),
            turn_rad_s=min(max(turn, -TURN_LIMIT_RAD_S), TURN_LIMIT_RAD_S),
        )
