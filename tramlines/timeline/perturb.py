"""Imperfect knowledge: what a ghost would know if it had measured the brain, not copied it.

ADR-0035, Result 1. The perfect ghost is a bit-exact copy and is always right (the
control). These functions blur a copied brain state the way a real measurement could
fail, so a ghost built from it shows how long prediction survives imperfect knowledge.

Every perturbation draws from its own generator, never the brain's, so the ghost's
future sensory input stays the same as the live fly's: the only difference between
them is the knowledge error.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import torch

from tramlines.brain.params import PARAMS
from tramlines.brain.state import BrainState

Kind = Literal["voltage", "drop_spike", "float32", "partial"]


@dataclass(frozen=True)
class Knowledge:
    """How the ghost's knowledge differs from the truth.

    - voltage: every voltage known only to within Gaussian noise of `amount` mV;
    - drop_spike: one spike in transit goes unobserved (`amount` is ignored);
    - float32: the whole state measured at single precision (`amount` is ignored);
    - partial: only a fraction `amount` of neurons is observed; the rest are
      assumed to be at rest.
    """

    kind: Kind
    amount: float = 0.0
    seed: int = 0

    def describe(self) -> str:
        if self.kind == "voltage":
            return f"voltage known to {self.amount:g} mV"
        if self.kind == "partial":
            return f"{self.amount:.1%} of neurons observed"
        return {"drop_spike": "one in-flight spike missed", "float32": "float32 precision"}[
            self.kind
        ]


def blur(state: BrainState, knowledge: Knowledge) -> None:
    """Apply `knowledge`'s error to `state` in place (call it on a fork's state)."""
    noise = torch.Generator(device="cpu").manual_seed(knowledge.seed)
    if knowledge.kind == "voltage":
        state.v_mV += knowledge.amount * torch.randn(
            state.v_mV.shape, generator=noise, dtype=torch.float64
        )
    elif knowledge.kind == "drop_spike":
        in_flight = torch.nonzero(state.in_flight)
        if len(in_flight):
            slot, neuron = in_flight[int(torch.randint(len(in_flight), (1,), generator=noise))]
            state.in_flight[int(slot), int(neuron)] = False
    elif knowledge.kind == "float32":
        state.v_mV.copy_(state.v_mV.to(torch.float32).to(torch.float64))
        state.g_mV.copy_(state.g_mV.to(torch.float32).to(torch.float64))
    elif knowledge.kind == "partial":
        unseen = (
            torch.rand(state.v_mV.shape, generator=noise, dtype=torch.float64) >= knowledge.amount
        )
        state.v_mV[unseen] = PARAMS.v_rest_mV
        state.g_mV[unseen] = 0.0
    else:
        raise ValueError(f"unknown kind of knowledge error: {knowledge.kind}")
