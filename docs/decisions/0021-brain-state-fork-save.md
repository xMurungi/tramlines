# 0021 — Brain state, forking, and saving to disk

- Status: Accepted (delegated)
- Date: 2026-10-22
- Phase: 2
- Decider: Claude (delegated)

## Context
[ADR-0008](0008-fork-shares-weights.md) locks the idea: a fork shares the wiring and copies the state. Phase 2 has to decide exactly what "the state" is, how a copy is made, how it is written to disk, and how we stop anyone from running a brain outside determinism mode ([ADR-0007](0007-determinism-first.md)).

## Options considered
1. **One `BrainState` dataclass holding every mutable tensor plus the random generator; `fork()` clones it; `save()` writes it with `torch.save` and reads it with `torch.load(weights_only=True)`.** Explicit, small, easy to test, safe to load.
2. **`copy.deepcopy` of the whole `Brain`.** One line, but copies the 182 MB wiring every time, and makes it easy for new mutable fields to hide anywhere.
3. **Pickle the `Brain` to disk.** Convenient, but loading a pickle can run arbitrary code, and the files would include the wiring.

## Decision
Option 1.

**State** (`tramlines/brain/state.py`), 5.83 MB for the full brain:

| Field | Type | Size | Meaning |
|---|---|---|---|
| `step` | int | — | steps run so far |
| `v_mV`, `g_mV` | float64 [138,639] | 1.1 MB each | voltage, synaptic input |
| `last_spike_step` | int64 [138,639] | 1.1 MB | drives refractoriness |
| `in_flight` | bool [18, 138,639] | 2.5 MB | spikes still travelling |
| `input_rates_hz` | float64 [inputs] | tiny | current sensory drive |
| `generator` | `torch.Generator` (state: 5 KB) | — | this timeline's randomness |

**Shared, never copied:** the connectome (182 MB), parameters, which neurons take input, and their refractory periods. `fork()` is a shallow copy of the `Brain` with a cloned state: 0.22 ms.

**Fingerprints.** `BrainState.fingerprint()` and `SpikeRecord.fingerprint()` are SHA-256 hashes of raw bytes. Raw bytes rather than values, so even −0.0 and 0.0 count as different. Two equal state fingerprints mean two identical futures.

**Saving.** One file per state (5.8 MB, 8 ms to save, 3 ms to load) with a format number, the connectome's fingerprint, the parameters and the input neurons. `Brain.load` refuses a file saved from different wiring or parameters.

**Determinism guard.** `Brain()` raises unless `enable_determinism()` has been called (deterministic algorithms, 1 thread).

## Consequences
- Adding any new mutable field to the engine means adding it to `BrainState`, `clone`, `fingerprint` and `save`/`load`; the sacred tests will fail otherwise.
- 5.83 MB is slightly above CLAUDE.md's 2–5 MB estimate. If many branches need it smaller, two easy savings exist: pack `in_flight` as bits (2.5 → 0.3 MB) and store `last_spike_step` as int32. Not needed yet.
- Saved states are tied to one connectome and one parameter set, by design.
- Bit-exactness is guaranteed on one machine. Different CPUs or library versions may round differently; comparing timelines across machines is not promised.

## For learners
To copy a running mind you copy *everything that changes* and *nothing that doesn't*. The hard part is being sure you found everything, including the hidden state of the random number generator. A fingerprint (a hash of every bit) lets a test check it instantly. Chapters 19 and 20 build this.
