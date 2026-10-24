# What it took to run

Every result here was computed on one laptop, using **two CPU cores** at a time. This page records what each study ran, how long it took, and how the number of cores is controlled, so anyone can plan a rerun. (The laptop's model and specifications are deliberately not recorded.)

## The brain being simulated
- **138,639 neurons** and **15,091,983 connections** (54,492,922 synapses), FlyWire v783 ([ADR-0013](../decisions/0013-data-files-and-source.md)).
- Time advances in steps of **0.1 ms**: one simulated second is **10,000 steps**. Updating every neuron at every step would be about 1.4 billion neuron updates per simulated second; the engine computes only the neurons not exactly at rest, with bit-identical results ([ADR-0027](../decisions/0027-awake-set-engine.md)).
- With the body and the world in the loop, one simulated second takes about **4 seconds** of computing while the fly simply walks (0.21–0.27× real time, [ADR-0036](../decisions/0036-walking-drive-upstream-of-p9.md)), and longer when the brain is busier: a perturbed 3-second ghost took about 35 s of computing in Result 1.

## Each study

| Study | What it ran | Simulated time | Time taken (2 cores) |
|---|---|---|---|
| Result 1, first pass ([ADR-0037](../decisions/0037-result-1-predictability-horizon.md)) | 3 moments × 15 ghosts, 3 s each | ~135 s | ~10 min |
| Result 1, second pass ([ADR-0038](../decisions/0038-result-1-second-pass.md)) | 270 ghosts × 3 s (3 seeds × 3 moments × 3 draws) | ~810 s | 79 min (9,396 s of CPU) |
| Result 2, null brains ([ADR-0039](../decisions/0039-result-2-null-brain.md)) | real + 5 null brains × 3 seeds; 10 s arena + five 1 s probes each | ~270 s | 15 min |
| Result 2, rewiring sweep | 7 rewiring levels × 3 brains, plus 75% and 90% | ~315 s | 22 + 9 min |
| Result 2, decoder-free check | 15 brains × 3 seeds × four 1 s situations | ~180 s | 14 min |
| Result 4, backward horizon ([ADR-0041](../decisions/0041-result-4-backward-horizon.md)) | 162 pairs of brains, each pair 2 × 3 s | ~972 s | 75 min (8,967 s of CPU) |
| Result 4, exact-arithmetic check | 400-neuron network, 1 s, float64 and 50 digits | 4 s | 12 s |
| Result 3, perturbation atlas ([plan](atlas-plan.md)) | 24 moments; ~62,000 single extra spikes screened for 30 ms; ~2,000 followed for 3 s; tipping points rerun under 3 decoders | ~11,000 s (estimate) | ~4½ h (running; exact figures added when it finishes) |
| Determinism gate ([ADR-0022](../decisions/0022-determinism-test-protocol.md)) | 1,057 bit-exact tests, 10 repeats | — | 10–13 min on 1 core |

## How the number of cores is set
- **One brain per process, one thread per brain.** Determinism mode fixes PyTorch to a single thread (`torch.set_num_threads(1)` in `enable_determinism`, [ADR-0007](../decisions/0007-determinism-first.md)), so each brain process uses exactly one core, and the results are bit-identical however many run side by side.
- **The study scripts take `--workers N`** (default 2): N brain processes in parallel, so N cores. For example:
  ```bash
  uv run python scripts/atlas_study.py --workers 2      # the default
  uv run python scripts/atlas_study.py --workers 1      # gentler on memory
  ```
  The viewer's server also stays at two: the projector and one ghost ([ADR-0033](../decisions/0033-phase-4-architecture.md), [ADR-0042](../decisions/0042-knowledge-slider.md)).
- **Why two:** memory, not processing. A brain process holds the connectome plus its state, about 1.3–4.5 GB, and up to 6.4 GB for scrambled brains in runaway activity. With two, memory pressure stayed normal or briefly "warning"; the rule is to drop to one worker if pressure stays at "warning" or swap keeps growing ([ADR-0029](../decisions/0029-divergence-batching-monitoring.md), [ADR-0032](../decisions/0032-decision-points.md)).

## How the machine was watched
- `scripts/monitor_system.py --label <name>` samples CPU, memory, memory pressure, swap and the thermal state every few seconds during a run and writes a summary (kept locally, not committed).
- Optionally, CPU power and frequency: `sudo powermetrics --samplers cpu_power,thermal -i 15000 -o <file>`. On Apple-chip Macs this reports power, frequency and thermal pressure, not temperatures or fan speed.
- What it showed across all the studies above: the thermal state stayed "nominal" (once "fair"), cores held full frequency (no throttling), CPU power about 15 W during a two-worker run, and memory pressure normal or briefly "warning" when other apps were busy.

## How long the project took (with an estimate for one person)
*The first two lines are measured from the repository's history; the per-part times are an estimate, not a measurement.*

- **Elapsed:** about two days of calendar time (first commit 22 October 2026, results merged 24 October 2026), over nine working sessions between one person (the owner, deciding direction) and an AI assistant (Claude, building), with breaks for sleep, usage limits and long runs. About 15 of those hours were the computer simply running the studies.
- **Output at that point:** about 12,000 lines of Python and TypeScript, 48 decision records, 127 commits, 35 merged pull requests, four controlled or pre-registered studies, a viewer, and this documentation.
- **Estimate for one skilled person working alone** (already fluent in Python, PyTorch, spiking neuron models and web development):

| Part | Estimated time |
|---|---|
| Engine matched spike for spike to the reference, plus determinism tests | 3–6 weeks |
| Body, world, senses and decoder, calibrated | 2–4 weeks |
| Server and viewer (ghost, knowledge slider, free-will fan) | 4–8 weeks |
| Four studies: design, debugging, analysis, write-ups | 2–4 months |
| Documentation, decision records, literature check, automated checks, reviews | 1–2 months |
| **Total** | **roughly 6–12 months** full time (less for a small team; much longer for a newcomer) |

Caveats: the direction and key judgements came from a person, and that part is not sped up; speed brought its own risks (two silent bugs and several overclaims were found and corrected, ADR-0038, 0041, 0039); and the write-up, release and expert review still take human time.
