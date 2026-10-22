"""The neuron model's parameters: the one place they live (CLAUDE.md section 13.1).

Values are those of the Shiu et al. reference code (`model.py`, `default_params`,
commit 91bdd1e7), verified line by line in ADR-0016. Every neuron uses the same
values; that is a simplification the honesty page states openly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class LIFParams:
    v_rest_mV: float = -52.0  # reference `v_0`
    v_reset_mV: float = -52.0  # reference `v_rst`
    v_threshold_mV: float = -45.0  # reference `v_th`; spike when v > v_th (strict)
    tau_membrane_ms: float = 20.0  # reference `t_mbr`
    tau_synapse_ms: float = 5.0  # reference `tau`
    refractory_ms: float = 2.2  # reference `t_rfc`; 0 for Poisson-stimulated neurons
    delay_ms: float = 1.8  # reference `t_dly`
    w_syn_mV: float = 0.275  # reference `w_syn`, per synapse
    poisson_scale: float = 250.0  # reference `f_poi`: one input event adds w_syn * f_poi to v
    dt_ms: float = 0.1  # Brian2 default clock

    def steps(self, duration_ms: float) -> int:
        """Whole time steps in a duration, rounded as Brian2's `timestep()` does."""
        return round(duration_ms / self.dt_ms)

    @property
    def refractory_steps(self) -> int:
        return self.steps(self.refractory_ms)

    @property
    def delay_steps(self) -> int:
        return self.steps(self.delay_ms)

    @property
    def poisson_kick_mV(self) -> float:
        return self.w_syn_mV * self.poisson_scale

    # Exact one-step solution of the two linear equations (Brian2 method='linear'):
    #   g' = g * decay_g
    #   v' = v_rest + (v - v_rest) * decay_v + g * g_to_v
    @property
    def decay_v(self) -> float:
        return math.exp(-self.dt_ms / self.tau_membrane_ms)

    @property
    def decay_g(self) -> float:
        return math.exp(-self.dt_ms / self.tau_synapse_ms)

    @property
    def g_to_v(self) -> float:
        tau_m, tau_s = self.tau_membrane_ms, self.tau_synapse_ms
        return tau_s / (tau_m - tau_s) * (self.decay_v - self.decay_g)


PARAMS = LIFParams()
