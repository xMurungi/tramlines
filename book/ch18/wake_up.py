# book: needs-data
"""Chapter 18: sugar on the tongue, and a whole fly brain answers."""

import math
from pathlib import Path

import pandas as pd
import torch

DATA = Path(__file__).resolve().parent.parent / "data"

# --- The model's numbers (Shiu et al. 2024) ---
V_REST, V_RESET, V_THRESHOLD = -52.0, -52.0, -45.0  # mV
TAU_V, TAU_G = 20.0, 5.0  # ms
DT = 0.1  # ms per step
REFRACTORY_STEPS = 22  # 2.2 ms
DELAY_STEPS = 18  # 1.8 ms
W_SYN = 0.275  # mV per synapse
KICK = W_SYN * 250  # mV added by one sensory input event

DECAY_V = math.exp(-DT / TAU_V)
DECAY_G = math.exp(-DT / TAU_G)
G_TO_V = TAU_G / (TAU_V - TAU_G) * (DECAY_V - DECAY_G)

# --- The wiring, grouped by sender ---
neurons = pd.read_csv(DATA / "Completeness_783.csv", index_col=0)
table = pd.read_parquet(
    DATA / "Connectivity_783.parquet",
    columns=["Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"],
)
n = len(neurons)
table = table.sort_values("Presynaptic_Index", kind="stable")
receiver = torch.tensor(table["Postsynaptic_Index"].to_numpy(), dtype=torch.int32)
weight = torch.tensor(table["Excitatory x Connectivity"].to_numpy(), dtype=torch.float64) * W_SYN
per_sender = torch.bincount(torch.tensor(table["Presynaptic_Index"].to_numpy()), minlength=n)
row_start = torch.cat([torch.zeros(1, dtype=torch.int64), torch.cumsum(per_sender, 0)])


def outgoing(senders):
    """Receivers and weights of every connection leaving `senders`."""
    starts = row_start[senders]
    counts = row_start[senders + 1] - starts
    first_slot = torch.cumsum(counts, 0) - counts
    positions = torch.repeat_interleave(starts - first_slot, counts)
    positions += torch.arange(positions.shape[0])
    return receiver[positions], weight[positions]


# --- Who we stimulate, and who we listen to ---
SUGAR = [
    720575940624963786, 720575940630233916, 720575940637568838, 720575940638202345,
    720575940617000768, 720575940630797113, 720575940632889389, 720575940621754367,
    720575940621502051, 720575940640649691, 720575940639332736, 720575940616885538,
    720575940639198653, 720575940639259967, 720575940617937543, 720575940632425919,
    720575940633143833, 720575940612670570, 720575940628853239, 720575940629176663,
    720575940611875570,
]
MN9 = 720575940660219265
sugar = torch.tensor([neurons.index.get_loc(r) for r in SUGAR])
mn9 = neurons.index.get_loc(MN9)

# --- The brain's state ---
v = torch.full((n,), V_REST, dtype=torch.float64)
g = torch.zeros(n, dtype=torch.float64)
last_spike = torch.full((n,), -(10**9), dtype=torch.int64)
in_flight = torch.zeros((DELAY_STEPS, n), dtype=torch.bool)
refractory = torch.full((n,), REFRACTORY_STEPS)
refractory[sugar] = 0  # stimulated neurons can fire every step
rng = torch.Generator().manual_seed(0)
p_input = 200.0 * DT / 1000.0  # 200 Hz

# --- One second of life: 10,000 steps ---
torch.use_deterministic_algorithms(True)
torch.set_num_threads(1)
counts = torch.zeros(n, dtype=torch.int64)
for step in range(10_000):
    active = (step - last_spike) >= refractory
    v = torch.where(active, (v - V_REST) * DECAY_V + g * G_TO_V + V_REST, v)
    g = torch.where(active, g * DECAY_G, g)

    fired = (v > V_THRESHOLD) & active
    fired_idx = torch.nonzero(fired).squeeze(1)
    last_spike[fired_idx] = step
    receptive = active & ~fired

    slot = step % DELAY_STEPS
    arriving = torch.nonzero(in_flight[slot]).squeeze(1)
    in_flight[slot] = fired
    if arriving.numel():
        post, w = outgoing(arriving)
        g.index_add_(0, post, w * receptive[post])

    hits = torch.rand(len(sugar), generator=rng, dtype=torch.float64) < p_input
    hits &= receptive[sugar]
    v.index_add_(0, sugar, hits.to(torch.float64) * KICK)

    v[fired_idx] = V_RESET
    g[fired_idx] = 0.0
    counts[fired_idx] += 1

print(f"sugar neurons fired on average {counts[sugar].double().mean():.1f} times")
print(f"neurons that fired at least once: {int((counts > 0).sum())}")
print(f"MN9 fired {int(counts[mn9])} times in one second")
