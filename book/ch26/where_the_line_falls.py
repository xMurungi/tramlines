# book: needs-data
"""Chapter 26: the fly's senses and motor decoder, laid out in the open."""

import torch

from tramlines.brain.neurons import load_catalog
from tramlines.world.arena import DEFAULT_ARENA
from tramlines.world.decoder import FlyDecoder
from tramlines.world.fly import FlyState
from tramlines.world.senses import FlySenses

catalog = load_catalog()
senses = FlySenses.from_catalog(catalog)
decoder = FlyDecoder.from_catalog(catalog)

print("SENSES (world -> brain)")
for name in ["sugar", "bitter", "loom_left", "loom_right", "walk_drive"]:
    print(f"  {name:11} {len(getattr(senses, name)):4} neurons")

on_food = FlyState(x_mm=18.0, y_mm=6.0)
nowhere = FlyState(x_mm=0.0, y_mm=0.0)
for label, fly in [("on food", on_food), ("on nothing", nowhere)]:
    rates = senses.rates_hz(fly, DEFAULT_ARENA)
    firing = int((rates > 0).sum())
    print(f"  {label:11} -> {firing} of {len(rates)} input neurons driven")

print("DECODER (brain -> body)")
#            P9 x4        DNa02 L, R  MDN x4      GF L, R   MN9 L, R
walking = [100.0] * 4 + [10.0, 30.0] + [0.0] * 4 + [0, 0] + [0, 0]
feeding = [100.0] * 4 + [10.0, 30.0] + [0.0] * 4 + [0, 0] + [60, 80]
escaping = [100.0] * 4 + [10.0, 30.0] + [0.0] * 4 + [100, 160] + [60, 80]
for label, rates in [("walking", walking), ("feeding", feeding), ("escaping", escaping)]:
    command = decoder.command(torch.tensor(rates, dtype=torch.float64), FlyState())
    print(
        f"  {label:9} speed {command.forward_mm_s:5.1f} mm/s  turn {command.turn_rad_s:+.2f} rad/s"
        f"  jump {command.jump_mm:4.1f} mm  feed {command.feed}"
    )
