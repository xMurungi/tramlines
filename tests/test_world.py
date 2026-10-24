"""The arena and the fly's body (ADR-0025)."""

import math

import pytest

from tramlines.world.arena import Arena, Loom, Patch
from tramlines.world.fly import FlyState, MotorCommand, step_fly

ARENA = Arena(radius_mm=10.0, patches=(Patch(5.0, 0.0, 1.0, "food"),))


def walk(command: MotorCommand, ms: int, fly: FlyState | None = None) -> FlyState:
    fly = fly or FlyState()
    for _ in range(ms):
        step_fly(fly, command, ARENA)
    return fly


def test_walks_straight_along_heading() -> None:
    fly = walk(MotorCommand(forward_mm_s=10.0), 500)
    assert fly.time_ms == 500
    assert fly.x_mm == pytest.approx(5.0)
    assert fly.y_mm == pytest.approx(0.0)


def test_turns_anticlockwise_for_positive_turn_rate() -> None:
    fly = walk(MotorCommand(turn_rad_s=math.pi), 500)  # half a second at 180°/s
    assert fly.heading_rad == pytest.approx(math.pi / 2)


def test_wall_stops_the_fly_at_the_edge() -> None:
    fly = walk(MotorCommand(forward_mm_s=50.0), 1000)
    assert math.hypot(fly.x_mm, fly.y_mm) == pytest.approx(ARENA.radius_mm)


def test_wall_does_not_pin_a_fly_heading_straight_at_it() -> None:
    fly = walk(MotorCommand(forward_mm_s=20.0), 2000)  # heading 0: straight at the wall
    assert math.hypot(fly.x_mm, fly.y_mm) == pytest.approx(ARENA.radius_mm)
    assert fly.y_mm != pytest.approx(0.0, abs=1.0)  # it slid along the wall instead of sticking


def test_feeding_fly_stands_still() -> None:
    fly = walk(MotorCommand(forward_mm_s=10.0, feed=True), 300)
    assert (fly.x_mm, fly.y_mm, fly.feeding) == (0.0, 0.0, True)


def test_jump_is_an_instant_hop() -> None:
    fly = walk(MotorCommand(jump_mm=3.0, jump_direction_rad=math.pi), 1)
    assert fly.x_mm == pytest.approx(-3.0)


def test_jump_needs_a_cooldown() -> None:
    fly = walk(MotorCommand(jump_mm=1.0), 300)  # asks to jump every millisecond
    assert fly.x_mm == pytest.approx(1.0)  # but only the first one happens
    assert fly.jump_cooldown_ms == 500 - 299


def test_patches_and_looms() -> None:
    assert ARENA.patches_under(5.5, 0.0)[0].kind == "food"
    assert not ARENA.patches_under(0.0, 0.0)
    loom = Loom(start_ms=100, duration_ms=10, direction_rad=0.0)
    assert [loom.progress(t) for t in (99, 100, 109, 110)] == [0.0, 0.1, 1.0, 0.0]


def test_clone_and_fingerprint() -> None:
    fly = walk(MotorCommand(forward_mm_s=7.0, turn_rad_s=1.0), 123)
    twin = fly.clone()
    assert twin.fingerprint() == fly.fingerprint()
    step_fly(twin, MotorCommand(forward_mm_s=1.0), ARENA)
    assert twin.fingerprint() != fly.fingerprint()
    assert fly.time_ms == 123


def test_strength_defaults_to_full() -> None:
    assert Patch(0.0, 0.0, 1.0, "food").strength == 1.0
    assert Loom(start_ms=0, duration_ms=10, direction_rad=0.0).strength == 1.0


def test_decision_arena_has_its_two_edges() -> None:
    from tramlines.world.arena import (
        DECISION_ARENA,
        FAINT_SHADOW_STRENGTH,
        LACED_BITTER_STRENGTH,
    )

    laced = [p for p in DECISION_ARENA.patches if p.kind == "bitter" and p.strength < 1.0]
    assert [p.strength for p in laced] == [LACED_BITTER_STRENGTH]
    food = next(p for p in DECISION_ARENA.patches if p.kind == "food")
    assert (laced[0].x_mm, laced[0].y_mm) == (food.x_mm, food.y_mm)  # the same spot: laced food
    assert DECISION_ARENA.looms[0].strength == FAINT_SHADOW_STRENGTH


def test_high_giant_fiber_during_cooldown_does_not_freeze_the_fly() -> None:
    import torch

    from tramlines.world.decoder import FlyDecoder

    decoder = FlyDecoder(readout_neurons=torch.arange(14))
    rates = torch.tensor([100.0] * 4 + [0.0, 0.0] + [0.0] * 4 + [150.0, 150.0] + [0.0, 0.0])
    ready = decoder.command(rates, FlyState(jump_cooldown_ms=0))
    recovering = decoder.command(rates, FlyState(jump_cooldown_ms=300))
    assert ready.jump_mm > 0
    assert recovering.jump_mm == 0 and recovering.forward_mm_s > 0


def test_decoder_thresholds_default_to_the_constants_and_scale_together() -> None:
    import torch

    from tramlines.world import decoder as d
    from tramlines.world.fly import FlyState

    base = d.FlyDecoder(readout_neurons=torch.arange(14))
    assert (base.gf_jump_hz, base.mn9_feed_start_hz, base.mn9_feed_stop_hz) == (
        d.GIANT_FIBER_JUMP_HZ,
        d.MN9_FEED_START_HZ,
        d.MN9_FEED_STOP_HZ,
    )
    high = base.scaled(1.2)
    assert high.gf_jump_hz == d.GIANT_FIBER_JUMP_HZ * 1.2
    assert high.mn9_feed_stop_hz == d.MN9_FEED_STOP_HZ * 1.2
    rates = torch.zeros(14, dtype=torch.float64)
    rates[10] = 55.0  # Giant Fiber at 55 Hz: above 50, below 60
    fly = FlyState()
    assert base.command(rates, fly).jump_mm > 0
    assert high.command(rates, fly).jump_mm == 0
