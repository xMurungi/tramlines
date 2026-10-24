# Backward horizon pilot: predictions written before results

Written 2026-10-24 while `scripts/backward_pilot.py` was running and before any of its
output existed. Decision dish, seed 0, Result 1's three moments; one small difference
made in the past; both timelines run 2 s side by side. "Identical" means the same
functional brain state, bit for bit (voltages, synaptic inputs, spikes in transit,
refractory neurons, random stream).

| Difference made in the past | walking (0.5 s) | laced food (1.2 s) | shadow (3.35 s) |
|---|---|---|---|
| voltages off by 10⁻⁹ mV | identical within ~0.5 s | identical within ~0.5 s, unless a spike flips | identical within ~0.5 s |
| voltages off by 10⁻³ mV | identical within ~1 s | **never** (spikes differ at once; Result 1) | identical within ~1 s |
| one spike in transit missed | identical within ~1 s | **never** (the fly's choice differs) | brain identical within ~1 s, **fly differs** |
| one extra spike | identical within ~1 s | **never** | brain identical within ~1 s, **fly differs** (it escapes) |

Reasoning:

- **Small differences decay.** Voltages leak with a 20 ms time constant, so a difference shrinks about e-fold every 20 ms. From 10⁻⁹ mV, it falls below the smallest step a 64-bit number can resolve near −50 mV (about 7 × 10⁻¹⁵ mV) in roughly 12 time constants, about 0.25 s. Then the two states become bit-identical. That time is set by the computer's precision, not by the brain. In exact arithmetic the difference would shrink forever without reaching zero.
- **At a threshold, differences grow instead.** At a decision the difference changes a spike and the fly's behaviour, and the record survives.
- **Expected pattern:** where the future is easy to predict, the past is erased; where the future is hard to predict, the past is kept. The past outlives the brain in the fly's body.
