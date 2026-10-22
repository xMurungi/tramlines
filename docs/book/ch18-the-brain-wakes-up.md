# Chapter 18 — The brain wakes up

> Touch sugar to a fly's leg and its proboscis swings down to drink. You are about to watch that happen inside a computer, in a brain made of 138,639 simulated neurons.

## Where we are
You have the wiring of a whole fly brain loaded and checked. This chapter gives every neuron the leaky integrate-and-fire rule from Chapter 10, connects them all, stimulates the sugar-tasting neurons, and listens to MN9, the motor neuron that extends the proboscis.

## The idea
Chapter 10's neuron had a voltage `v` that leaked back to rest and fired at a threshold. Chapter 11 gave neurons a second number, `g`, the input arriving through synapses, which decays on its own. Now we do the same for all 138,639 neurons at once, every tenth of a millisecond.

Each step, in this exact order:

1. **Integrate.** Every neuron's `v` and `g` move one step forward in time, using the exact solution of their equations (no rounding-off "Euler" step).
2. **Fire.** Neurons whose voltage is above −45 mV fire, unless they are *refractory*, still recovering from their last spike (2.2 ms).
3. **Deliver.** Spikes fired 1.8 ms ago (18 steps) arrive. Each adds its weight to the receiver's `g`. Sugar neurons also get their random "taste" kicks.
4. **Reset.** Neurons that fired drop back to −52 mV with `g` cleared.

Think of a stadium wave. Each person only watches their neighbours, and acts after a short delay. Nobody sees the whole wave, yet the wave travels. A brain is like that, with 54 million "neighbours" relationships.

One detail cost us an afternoon, and it is worth knowing: **a refractory neuron ignores input entirely.** Spikes that arrive while it recovers are lost, not saved for later. We first assumed the opposite from reading the reference code. Then we ran the reference simulator on a two-neuron network and watched what it actually did ([ADR-0016](../decisions/0016-verified-neuron-model.md)). Getting it wrong changed about 4% of all spikes in our test networks.

## Build it
Save as `ch18/wake_up.py`. It is long, but every part is something you have built before.

```python
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
```

## Run it

```bash
uv run python ch18/wake_up.py
```

It takes about ten seconds: ten thousand steps, each touching 138,639 neurons.

```text
sugar neurons fired on average 192.2 times
neurons that fired at least once: 388
MN9 fired 98 times in one second
```

## The click
Nobody told MN9 to fire. You poked 21 sugar-sensing neurons, and the signal found its own way through a wiring diagram that nobody designed, only measured, to the one motor neuron that makes a fly drink. Out of 138,639 neurons, only 388 joined in. The rest stayed quiet.

Now run it again. You get **98** again, and 388 again. The sugar input is random, but the randomness comes from a generator started at seed 0, so it is the *same* randomness every time (you met this in Chapter 12). This brain is deterministic. Hold on to that; it is the whole secret of the machine in Part IV.

Finally, the real experiment. Instead of one run at 200 Hz, the project runs ten seeds at each of twelve stimulation rates (`scripts/sugar_mn9.py`):

![MN9 firing rate against sugar stimulation rate: zero up to 20 Hz, switching on around 30 to 40 Hz, rising steeply to 80 Hz, levelling off near 90 Hz at 200 Hz. A second line, the matching motor neuron on the other side, follows the same shape at about two thirds of the rate.](../assets/sugar_mn9_reference.png)

Below about 30 Hz, nothing. Then MN9 switches on and climbs, and finally saturates. This is the result Shiu and colleagues published in *Nature* in 2024, and the reference simulator, run on the same data, gives the same numbers within noise ([ADR-0020](../decisions/0020-sugar-mn9-regression-bands.md)). You have reproduced a *Nature* result on your laptop.

## Break it

1. Change `200.0` to `20.0` in `p_input`. Predict MN9's count, then run.
2. Flip the signs: multiply `weight` by `-1`. What happens to activity, and why?
3. Change the seed to `1`. Is MN9's count the same? Run seed 1 twice: is it the same *as itself*?
4. Delete the `* receptive[post]` (so refractory neurons keep their input). Does MN9's count change? This is the detail from "The idea".

## When it goes wrong

- **It runs for minutes.** Make sure `torch.set_num_threads(1)` is there; on some machines many threads are slower for many small operations. Also check you did not convert `receiver` to a Python list.
- **MN9 fires 0 times at 200 Hz.** Most likely `KICK` was added to `g` instead of `v`, or `refractory[sugar] = 0` is missing. The sugar neurons themselves should fire about 190 times.
- **Different numbers from the book.** Check `DELAY_STEPS`, the strict `>` in the threshold, and the order of the four phases. Order matters: firing must be decided before arrivals are added.

## Check yourself

1. In what order do the four phases of a step happen, and why does the order matter?
2. Why is the run identical every time even though the input is random?
3. What happens to a spike that arrives at a refractory neuron?
4. Why do only a few hundred neurons fire?

??? note "Answers"
    1. Integrate, fire, deliver, reset. If arrivals were added before firing was decided, spikes would act a step early; if reset came before delivery, arrivals to a firing neuron would survive. The reference simulator uses this order, and we match it exactly.
    2. The random numbers come from a generator with a fixed seed: the same sequence every run.
    3. It is lost. Refractory neurons ignore all input, as the reference simulator does.
    4. The stimulus reaches only the circuits downstream of sugar sensing; inhibition and thresholds keep the rest quiet.

## Decisions in this chapter

- [ADR-0003: the leaky integrate-and-fire model](../decisions/0003-neuron-model-shiu-lif.md)
- [ADR-0014: where the reference code differs from our first description](../decisions/0014-challenge-reference-model-details.md)
- [ADR-0016: the model, verified spike for spike](../decisions/0016-verified-neuron-model.md)
- [ADR-0018: event-driven delivery](../decisions/0018-event-driven-engine.md)
- [ADR-0020: the result and its tests](../decisions/0020-sugar-mn9-regression-bands.md)

## Next
The brain is deterministic; in Chapter 19 you will capture *everything* it is at one instant, so you can copy it.
