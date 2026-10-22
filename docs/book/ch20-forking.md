# Chapter 20 — Forking

> Copy a mind mid-thought. Let the copy go on alone. Does it know it is a copy? Does it matter?

## Where we are
You can name every piece of a brain's state. This chapter copies it, the move called a **fork**, and checks that the copy lives exactly the same future as the original.

## The idea
A fork is two lines of code: share the wiring, clone the state.

```python
def fork(self) -> Brain:
    twin = copy.copy(self)  # shares connectome, params, input_neurons, refractory_steps
    twin.state = self.state.clone()
    return twin
```

`copy.copy` makes a shallow copy: a new `Brain` whose fields point at the *same* objects as the original's. That is what we want for the wiring. Then we replace the state with a deep clone: new tensors with the same numbers, and a new random generator set to the same position.

From then on, the two brains are separate. Run one and the other does not move. But because they start from the same state and get the same inputs, the [determinism](glossary.md) you met in Chapter 12 says they must do the same thing, forever.

Science fiction has played with this for decades: a mind copied, the copy waking up believing it is the original. Here it is literal, and small enough to test. Two flies, one past, one future.

## Build it
Save as `ch20/fork.py`:

```python
"""Chapter 20: copy a mind without copying its wiring."""

from tramlines.brain.connectome import load_connectome
from tramlines.brain.engine import Brain, enable_determinism
from tramlines.brain.neurons import REFERENCE_SUGAR_GRNS, load_catalog

enable_determinism()
sugar = load_catalog().index_of(REFERENCE_SUGAR_GRNS)
brain = Brain(load_connectome(), sugar, seed=7)
brain.set_input_rates(200.0)
brain.run(300)  # 30 ms

twin = brain.fork()
print("shares the wiring:", twin.connectome is brain.connectome)
print("has its own voltages:", twin.state.v_mV is not brain.state.v_mV)

a = brain.run(700)  # 70 ms more, each on its own
b = twin.run(700)
print(f"original: {a.neurons.numel()} spikes, twin: {b.neurons.numel()} spikes")
print("identical spikes:", a.fingerprint() == b.fingerprint())
print("identical final state:", brain.state.fingerprint() == twin.state.fingerprint())

# Now nudge the twin: one sugar neuron fires one extra time.
nudged = brain.fork()
nudged.state.v_mV[int(sugar[0])] = 0.0
c = brain.run(700)
d = nudged.run(700)
print(f"after one extra spike: {c.neurons.numel()} spikes vs {d.neurons.numel()} spikes")
print("identical spikes:", c.fingerprint() == d.fingerprint())
```

## Run it

```bash
uv run python ch20/fork.py
```

```text
shares the wiring: True
has its own voltages: True
original: 1277 spikes, twin: 1277 spikes
identical spikes: True
identical final state: True
after one extra spike: 1229 spikes vs 1199 spikes
identical spikes: False
```

## The click
Two brains, run one after the other, each with its own voltages and its own random generator, produced the same 1,277 spikes at the same moments in the same neurons. Not similar: identical down to the last bit of every voltage. The fork took a fifth of a millisecond.

Then the last three lines. One sugar neuron was pushed to fire once more, a single event among millions. In the next 70 ms the two brains fired 1,229 and 1,199 spikes. One spike did not stay one spike. It rippled.

Hold both results in your mind at once, because the rest of the project is built from them. *Copy the state exactly, and the future is copied exactly.* That is the ghost (Chapter 22). *Change one spike, and the future can split.* That is free will (Chapter 23).

## Break it

1. Fork, then give the twin a different input rate (`twin.set_input_rates(100.0)`). Do they stay identical?
2. Fork, then call `twin.state.generator.manual_seed(1)`. Same state, different randomness. What happens?
3. Instead of `fork()`, try `twin = copy.copy(brain)` with no state clone. Run the twin, then look at the original's `state.step`. What went wrong?
4. Nudge a neuron that is *not* a sugar neuron (say neuron 100). Does the future still change?

## When it goes wrong

- **The two brains differ when they should not.** Something mutable is shared, or something was left out of the clone. The usual culprit is the random generator: cloning tensors but not `generator.get_state()`.
- **The original changed when you ran the twin.** You copied the `Brain` but not its state; both point at the same tensors.
- **Out of memory with many forks.** Check you are not deep-copying the connectome. `twin.connectome is brain.connectome` must be `True`.

## Check yourself

1. What does a fork share, and what does it copy?
2. Why is `copy.copy` (shallow) right for the brain but wrong for the state?
3. Two forks get different input rates. Should they stay identical?
4. Why can one extra spike change the number of spikes that follow?

??? note "Answers"
    1. It shares the wiring, parameters and input neuron list; it copies the state, including the random generator.
    2. Shallow copying shares objects. Sharing the never-changing wiring saves memory; sharing the state would mean running one brain moves the other.
    3. No. Same state but different inputs: their futures are allowed to differ, and will.
    4. The extra spike reaches other neurons, nudging some over threshold or delaying others, and each of those changes spreads further.

## Decisions in this chapter

- [ADR-0008: forks share the wiring](../decisions/0008-fork-shares-weights.md)
- [ADR-0021: state, fork, save](../decisions/0021-brain-state-fork-save.md)

## Next
"Identical" is a big claim; in Chapter 21 you will prove it three different ways, a hundred times over.
