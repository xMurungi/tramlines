"""The senses scale with patch and shadow strength (ADR-0028, ADR-0032)."""

import math

import pytest
import torch

from tramlines.brain.data import DATA_DIR
from tramlines.brain.neurons import ANNOTATIONS_FILE, load_catalog
from tramlines.world.arena import Arena, Loom, Patch
from tramlines.world.fly import FlyState
from tramlines.world.senses import BITTER_HZ, LOOM_MAX_HZ, SUGAR_HZ, WALK_DRIVE_HZ, FlySenses

pytestmark = pytest.mark.skipif(
    not (DATA_DIR / ANNOTATIONS_FILE).exists(), reason="needs fetch_data.py"
)


def port_rates(senses: FlySenses, rates: torch.Tensor) -> dict[str, set[float]]:
    out, start = {}, 0
    for name in ["sugar", "bitter", "loom_left", "loom_right", "walk_drive"]:
        n = len(getattr(senses, name))
        out[name] = set(rates[start : start + n].tolist())
        start += n
    return out


def test_laced_food_and_faint_shadow_scale_the_rates() -> None:
    senses = FlySenses.from_catalog(load_catalog())
    arena = Arena(
        radius_mm=40.0,
        patches=(Patch(0.0, 0.0, 5.0, "food"), Patch(0.0, 0.0, 5.0, "bitter", strength=0.5)),
        looms=(Loom(start_ms=0, duration_ms=10, direction_rad=math.pi / 2, strength=0.25),),
    )
    fly = FlyState(time_ms=9, heading_rad=0.0)  # loom fully grown, coming from the fly's left
    rates = port_rates(senses, senses.rates_hz(fly, arena))
    assert rates["sugar"] == {SUGAR_HZ}
    assert rates["bitter"] == {BITTER_HZ * 0.5}
    assert rates["loom_left"] == {LOOM_MAX_HZ * 0.25}
    assert rates["loom_right"] == {0.0}
    assert rates["walk_drive"] == {WALK_DRIVE_HZ}
