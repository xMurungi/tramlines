# Chapter 21 — The sacred tests

> The ghost must never be wrong, not once. How do you prove a "never"?

## Where we are
You can fork a brain and watch two copies live the same life. This chapter turns that observation into proof: tests that fail if two timelines ever differ by a single bit, run every time the code changes.

## The idea
"The two brains are the same" can mean many things: the same number of spikes, roughly the same voltages, the same behaviour. We mean the strongest version: **the same bits, all of them.** Every spike at the same step in the same neuron, every voltage equal down to the last binary digit, the random generator at the same position.

Comparing millions of numbers one by one is slow and easy to get wrong, so we use a [hash](glossary.md) (Chapter 17). Feed every byte of the spike record and of the final state into SHA-256, and compare the two 64-character results. Equal fingerprints mean identical futures.

There are three ways to arrive at "the same moment", and each can fail differently:

1. **Fork** in memory. Fails if something mutable is shared or left out of the copy.
2. **A fresh process** given the same seed: a whole new Python, sharing nothing. Fails if anything depends on the order things happen in memory, on threads, or on hidden global randomness.
3. **Save and load** through a file on disk. Fails if anything is lost or changed on the way.

Then we test the tests. A test that always passes proves nothing. So we also check that a fork with *different* randomness, or one extra spike, produces a *different* fingerprint. A smoke alarm is only useful if you have seen it go off.

## Build it
Save as `ch21/sacred.py`:

```python
"""Chapter 21: three ways to start from the same moment, and proof they agree."""

import subprocess
import sys
import tempfile
from pathlib import Path

from tramlines.brain.connectome import load_connectome
from tramlines.brain.engine import Brain, enable_determinism
from tramlines.brain.neurons import REFERENCE_SUGAR_GRNS, load_catalog

enable_determinism()
wiring = load_connectome()
sugar = load_catalog().index_of(REFERENCE_SUGAR_GRNS)


def future(seed: int) -> str:
    """Run 50 ms of sugar from the start and fingerprint everything that happened."""
    brain = Brain(wiring, sugar, seed=seed)
    brain.set_input_rates(200.0)
    return brain.run(500).fingerprint() + brain.state.fingerprint()


if sys.argv[1:] == ["child"]:  # the fresh-process copy of this program
    print(future(seed=3))
    sys.exit()

# (a) Fork in the middle; both halves must agree.
brain = Brain(wiring, sugar, seed=3)
brain.set_input_rates(200.0)
brain.run(200)
twin = brain.fork()
same = brain.run(300).fingerprint() == twin.run(300).fingerprint()
print("fork:          ", "identical" if same else "DIFFERENT")

# (b) A brand-new Python process, sharing nothing with this one.
child = subprocess.run([sys.executable, __file__, "child"], capture_output=True, text=True)
same = child.stdout.strip() == future(seed=3)
print("fresh process: ", "identical" if same else "DIFFERENT")

# (c) Save to disk at 20 ms, load into a new brain, continue.
brain = Brain(wiring, sugar, seed=3)
brain.set_input_rates(200.0)
brain.run(200)
path = Path(tempfile.mkdtemp()) / "moment.pt"
brain.save(path)
restored = Brain.load(path, wiring)
same = brain.run(300).fingerprint() == restored.run(300).fingerprint()
print("save and load: ", "identical" if same else "DIFFERENT")
```

## Run it

```bash
uv run python ch21/sacred.py
```

```text
fork:           identical
fresh process:  identical
save and load:  identical
```

The project's real version is `tests/test_determinism.py`. It runs all three, for ten seeds, on both a small test network and the whole brain, with input rates that change every 10 ms the way the world will change them. For the Phase 2 gate it ran everything ten times over: **100 out of 100** for every property ([ADR-0022](../decisions/0022-determinism-test-protocol.md)).

## The click
This is the promise the whole machine makes, written as code. When the ghost in Chapter 22 walks ahead of the fly, the viewer is trusting these three lines. If any of them ever printed `DIFFERENT`, the ghost could be wrong, and a ghost that is sometimes wrong is just a guess.

Notice what you did *not* have to do: no physics, no philosophy. Determinism here is an engineering property, earned by choices made in earlier chapters. One random generator per timeline, its state saved with everything else, one thread, deterministic arithmetic, a fixed order of operations. Remove any one and these tests catch it.

That is also why the project's honesty page says this is a property of the *simulation*, not a claim about real flies ([honesty](../honesty.md)). We built it in on purpose.

## Break it

1. In the child branch, change `seed=3` to `seed=4`. What does test (b) print? Is that a bug in the engine or in the test?
2. After loading, call `restored.set_input_rates(199.0)`. What happens to (c)?
3. Remove `enable_determinism()`. What does the engine do, and why is that better than silently continuing?
4. In the project, run `uv run pytest tests/test_determinism.py -k diverges` and read the two negative controls.

## When it goes wrong

- **(b) fails but (a) passes.** Something depends on the process: a global random number generator, the order of a Python `set`, or the thread count. Look for randomness that does not come from the timeline's own generator.
- **(c) fails.** A field is missing from `save`/`load`. Compare `brain.state.fingerprint()` with `restored.state.fingerprint()` immediately after loading.
- **Everything fails after an upgrade.** A new library version may round differently. Fingerprints are only promised on one machine with one set of versions; re-run the tests and record the new numbers.

## Check yourself

1. What exactly does "identical" mean in these tests?
2. Why compare fingerprints rather than spike counts?
3. What kind of mistake does the fresh-process test catch that the fork test cannot?
4. Why does the project test that a *different* timeline gives a *different* fingerprint?

??? note "Answers"
    1. Every spike (neuron and step) and every byte of the final state, including the random generator, are the same.
    2. Two runs can have the same spike count and different spikes. A fingerprint changes if anything at all differs.
    3. Hidden dependence on the process: global random state, memory order, threads. A fork lives in the same process, so it would share those.
    4. To prove the test can fail. A test that cannot fail proves nothing.

## Decisions in this chapter

- [ADR-0007: determinism first](../decisions/0007-determinism-first.md)
- [ADR-0021: state, fork, save](../decisions/0021-brain-state-fork-save.md)
- [ADR-0022: the sacred tests](../decisions/0022-determinism-test-protocol.md)

## Next
You have proved a copy can live the same future; in Chapter 22 you will send one ahead in time, and it will show the fly where it is going.
