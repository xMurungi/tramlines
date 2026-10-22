# Chapter 19 — State

> If you froze a brain mid-thought and wrote down everything about it, how long would the list be?

## Where we are
Your brain runs and tastes sugar. This chapter separates what a brain *is* (its wiring, fixed forever) from what a brain is *doing* (its state, which changes every tenth of a millisecond), and measures both.

## The idea
In Chapter 18 everything lived in loose variables: `v`, `g`, `last_spike`, `in_flight`, a random generator. Look at them again and sort them into two piles:

- **Never changes:** the wiring (who connects to whom, and how strongly), the model's numbers, which neurons receive sensory input.
- **Changes every step:** voltages, synaptic inputs, when each neuron last fired, the spikes still travelling down axons, the current input rates, and the position of the random generator in its sequence.

The second pile is the brain's **state**. Here is the claim this whole part of the book rests on: *the wiring plus the state determine the entire future.* Nothing else matters. So if you copy the state exactly, you have copied the moment.

Think of a chess game. The board's rules never change. The position of the pieces, plus whose turn it is, is everything you need to continue the game. Write down the position and anyone can pick up where you left off. One easy thing to forget: the random generator is part of the position too. It is like a deck of cards that has been half dealt: you need to know which card comes next.

The project gathers the state into one object, `BrainState`, in `tramlines/brain/state.py`, and the wiring into another, `Connectome`. The engine from Chapter 18, reorganised into these pieces, lives in `tramlines/brain/engine.py`.

## Build it
Save as `ch19/anatomy_of_a_moment.py`:

```python
"""Chapter 19: everything a brain is at one instant."""

from tramlines.brain.connectome import load_connectome
from tramlines.brain.engine import Brain, enable_determinism
from tramlines.brain.neurons import REFERENCE_SUGAR_GRNS, load_catalog

enable_determinism()
wiring = load_connectome()
brain = Brain(wiring, load_catalog().index_of(REFERENCE_SUGAR_GRNS), seed=0)
brain.set_input_rates(200.0)
brain.run(500)  # 50 ms of sugar

state = brain.state
print(f"the brain after {state.step} steps ({state.step / 10:.0f} ms):")
for name, tensor in [
    ("voltage", state.v_mV),
    ("synaptic input", state.g_mV),
    ("last spike", state.last_spike_step),
    ("spikes in flight", state.in_flight),
    ("input rates", state.input_rates_hz),
]:
    size = tensor.numel() * tensor.element_size()
    print(f"  {name:17} {str(list(tensor.shape)):16} {size / 1e6:5.2f} MB")
print(f"  random generator  {state.generator.get_state().numel():,} bytes of hidden state")
print(f"state in total:  {state.nbytes() / 1e6:.2f} MB")
wiring_bytes = sum(t.numel() * t.element_size() for t in (wiring.row_start, wiring.post, wiring.weight_mV))
print(f"wiring in total: {wiring_bytes / 1e6:.2f} MB (never changes)")

refractory = int(((state.step - state.last_spike_step) < brain.refractory_steps).sum())
print(f"right now: {refractory} neurons recovering, {int(state.in_flight.sum())} spikes travelling")
```

## Run it

```bash
uv run python ch19/anatomy_of_a_moment.py
```

```text
the brain after 500 steps (50 ms):
  voltage           [138639]          1.11 MB
  synaptic input    [138639]          1.11 MB
  last spike        [138639]          1.11 MB
  spikes in flight  [18, 138639]      2.50 MB
  input rates       [21]              0.00 MB
  random generator  5,056 bytes of hidden state
state in total:  5.83 MB
wiring in total: 182.21 MB (never changes)
right now: 27 neurons recovering, 30 spikes travelling
```

## The click
A fly brain, at one instant, is **5.83 megabytes**. About the size of one photo on your phone.

The wiring is thirty times larger, but it never changes. That asymmetry is the key that unlocks the rest of the machine. To make a copy of this brain in this exact moment, you do not copy 188 MB. You copy 5.83 MB and point at the same wiring. A hundred possible futures cost about 580 MB, not 18 GB.

And look at the last line: 30 spikes are "in the air" right now, fired but not yet arrived. They are invisible if you only look at voltages, yet they will shape the next 1.8 ms. Leave them out of a copy and the copy's future would quietly differ. Every piece of state matters.

## Break it

1. Run for 1,000 steps instead of 500. Does the state get bigger? Why not?
2. Set the input rate to `0.0`. How many spikes are in flight? How many neurons are recovering?
3. Print `state.fingerprint()` twice, with a `brain.run(1)` between. What changed?
4. Find the largest voltage in the brain right now with `state.v_mV.max()`. Is it above threshold? Can it be?

## When it goes wrong

- **`RuntimeError: call ... enable_determinism() first`.** The engine refuses to run outside determinism mode ([ADR-0021](../decisions/0021-brain-state-fork-save.md)). Call `enable_determinism()` before making a `Brain`.
- **`ModuleNotFoundError: tramlines`.** Run with `uv run` from inside the project, so its own package is available.
- **Sizes differ from the book.** Make sure the dtypes match: float64 for voltages, int64 for spike times, bool for spikes in flight.

## Check yourself

1. Which belongs to the state: the synapse weights, or the spikes in flight?
2. Why is the random generator part of the state?
3. Why is the state so much smaller than the wiring?
4. What would go wrong if you copied everything except the spikes in flight?

??? note "Answers"
    1. The spikes in flight. The weights never change.
    2. The next random numbers depend on where the generator is in its sequence. Two copies at different positions would get different sensory input.
    3. The state has a few numbers per neuron; the wiring has a number per *connection*, and there are 15 million connections.
    4. The copy would miss spikes about to arrive. For up to 1.8 ms it would receive less input than the original, and their futures would split.

## Decisions in this chapter

- [ADR-0008: forks share the wiring](../decisions/0008-fork-shares-weights.md)
- [ADR-0021: what the state contains](../decisions/0021-brain-state-fork-save.md)

## Next
You know exactly what a moment is; in Chapter 20 you will copy one, and watch two brains live the same life.
