# 0022 — The sacred tests: what "identical" means and how it is proved

- Status: Accepted (delegated)
- Date: 2026-10-22
- Phase: 2
- Decider: Claude (delegated)

## Context
CLAUDE.md Phase 2 asks for three bit-exact tests (fork, separate processes, save/load) passing 100/100 across 10 seeds, and 13.2 says `tests/test_determinism.py` runs on every change and is never weakened, skipped or marked flaky. The full brain costs about 1 s per 100 ms simulated, so the protocol must be strict *and* fast enough to run every time.

## Options considered
1. **Fingerprints of the full raster and full final state, two scenario sizes, inputs that change on a schedule, plus negative controls; 10 seeds every run, and a repeat count for the 100/100 gate.**
2. **Compare only spike counts or a few neurons.** Cheap, but blind to most differences.
3. **Only the full brain, 100 runs every time.** Strict, but about 10 minutes per change, which would push people to skip it.

## Decision
Option 1, in `tests/test_determinism.py`.

- **Identical** = equal SHA-256 of the whole spike raster *and* of every byte of the final state, including the random generator's state.
- **Scenarios.** `small`: 400 neurons, 20 Poisson inputs, 300 ms, needs no data, so it runs even on a fresh clone. `full`: the whole v783 brain with the 21 sugar GRNs, 100 ms, run whenever the data is present.
- **Inputs change every 10 ms** (200, 0, 80, 150, 30 Hz, repeating), the way the world will drive them. The fork point differs per seed and is deliberately not on a schedule boundary.
- **(a) Fork:** run to the fork point, fork, run both to the end. Also checks the wiring is shared, not copied.
- **(b) Fresh process:** a new Python interpreter runs all 10 seeds and must print the same fingerprints as the test process.
- **(c) Save/load:** save at the fork point, load into a new brain, continue.
- **Negative controls:** re-seeding a fork's generator, or forcing one extra spike, *must* change the raster. They prove the tests can see a difference. Two more tests check that a fork never changes the original, and that loading refuses different wiring.
- **Every change:** 10 seeds × 2 scenarios × 3 properties, about 1 minute. **The gate:** `TRAMLINES_DETERMINISM_REPEATS=10 uv run pytest tests/test_determinism.py` repeats everything 10 times, giving 100 runs per property per scenario.

## Consequences
- A failure is never "flaky". It means a timeline leaked or a computation stopped being deterministic, and everything stops until it is understood.
- Phase 3 adds world state to the scenarios; the fingerprints must then cover the world too.
- The 100-repeat gate is run at phase gates and after any engine change, and its result recorded in the journal.

## For learners
"Identical" is a strong word, so we define it precisely: the same bits, all of them. And we test the test. A check that passes no matter what proves nothing, so we deliberately make one timeline different and confirm the test notices. Chapter 21 walks through these tests.
