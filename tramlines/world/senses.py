"""World → brain: which neurons the fly senses with, and how strongly (ADR-0028).

Every port is a set of v783 neurons found by annotation (release v2.1.0) that
receive Poisson input at a rate the world sets. Stimulating a neuron forces it
to fire at roughly that rate, like optogenetics; this is a design choice of the
project, not the fly's own sense organs (honesty page).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch

from tramlines.brain.neurons import REFERENCE_SUGAR_GRNS, NeuronCatalog
from tramlines.world.arena import Arena
from tramlines.world.fly import FlyState

# Rates (Hz). Evidence: port survey and sugar + bitter check (ADR-0023).
SUGAR_HZ = 150.0  # on food: drives MN9 strongly (Phase 1 curve saturates above 100 Hz)
BITTER_HZ = 150.0  # on a bitter patch: abolishes sugar-driven MN9 at equal rates
LOOM_MAX_HZ = 200.0  # a looming shadow ramps LPLC2 from 0 to this as it arrives
WALK_DRIVE_HZ = 100.0  # tonic drive to P9: the brain is silent without input (ADR-0028)


@dataclass(frozen=True)
class FlySenses:
    """The five ports chosen in ADR-0028, as engine indices."""

    sugar: torch.Tensor
    bitter: torch.Tensor
    loom_left: torch.Tensor
    loom_right: torch.Tensor
    walk_drive: torch.Tensor

    @classmethod
    def from_catalog(cls, catalog: NeuronCatalog) -> FlySenses:
        def lplc2(side: str) -> torch.Tensor:
            return catalog.index_of(catalog.find(hemibrain_type="LPLC2", side=side))

        return cls(
            sugar=catalog.index_of(REFERENCE_SUGAR_GRNS),
            bitter=catalog.index_of(catalog.find(cell_class="gustatory", cell_sub_class="bitter")),
            loom_left=lplc2("left"),
            loom_right=lplc2("right"),
            walk_drive=catalog.index_of(catalog.find(hemibrain_type="DNp09")),  # P9
        )

    def _ports(self) -> tuple[torch.Tensor, ...]:
        return (self.sugar, self.bitter, self.loom_left, self.loom_right, self.walk_drive)

    @property
    def input_neurons(self) -> torch.Tensor:
        return torch.cat(self._ports())

    def rates_hz(self, fly: FlyState, arena: Arena) -> torch.Tensor:
        # Overlapping patches of one kind: the strongest counts.
        taste = {"food": 0.0, "bitter": 0.0}
        for patch in arena.patches_under(fly.x_mm, fly.y_mm):
            taste[patch.kind] = max(taste[patch.kind], patch.strength)
        loom_left = loom_right = 0.0
        active = arena.active_loom(fly.time_ms)
        if active is not None:
            loom, progress = active
            # Where the shadow comes from, relative to where the fly faces:
            # positive = on its left (angles grow anticlockwise).
            relative = math.remainder(loom.direction_rad - fly.heading_rad, math.tau)
            drive = LOOM_MAX_HZ * progress * loom.strength
            if relative >= 0:
                loom_left = drive
            else:
                loom_right = drive
        per_port = (
            SUGAR_HZ * taste["food"],
            BITTER_HZ * taste["bitter"],
            loom_left,
            loom_right,
            WALK_DRIVE_HZ,
        )
        return torch.cat(
            [
                torch.full((len(neurons),), rate, dtype=torch.float64)
                for neurons, rate in zip(self._ports(), per_port, strict=True)
            ]
        )
