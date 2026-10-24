# XXXX — The free-will fan: one moment, eight futures, one aimed spike apart

- Status: Accepted (delegated)
- Date: 2026-10-24
- Phase: 5
- Decider: Claude (delegated, within ADR-0033's architecture, the owner-approved [ADR-0031](0031-proposal-aimed-free-will.md) and owner decision 9)

## Context
CLAUDE.md Phase 5: a FREE WILL button forks N branches (owner decision 9 keeps N = 8), each with one extra spike, logged and shown, all run H = 3 s ahead; divergence is measured three ways (path distance, spike-raster Hamming distance, time to divergence), and the fan shows which branches re-converge and which never do. [ADR-0031](0031-proposal-aimed-free-will.md) (owner-approved) aims the spike at a neuron *currently receiving input* and offers the button at *decision moments*, because a spike anywhere else almost never changes anything in this model ([ADR-0029](0029-divergence-batching-monitoring.md)). [ADR-0032](0032-decision-points.md) and [ADR-0036](0036-walking-drive-upstream-of-p9.md) measured what aimed spikes do at the decision dish's moments: at the laced food 16/16 paths diverge; under the shadow, 14/16 flies escape while their brains' spikes re-converge.

Constraints: keep ADR-0033 / [ADR-0042](0042-knowledge-slider.md)'s architecture (projector + one ghost process, one job at a time, per-viewer outboxes, cache keys that include everything that changes results); at most two brain processes ([ADR-0032](0032-decision-points.md)); a spike the engine refuses must be reported, never silently become a copy ([ADR-0041](0041-result-4-backward-horizon.md)).

## Options considered
**Where the fan is computed**

1. **The existing ghost process, one fan per job, results streamed** (chosen). The job loads the checkpoint behind the moment, runs untouched to the moment, aims the spikes, then runs the untouched future and each branch in turn, sending each as it finishes. Pros: still two brain processes; the untouched future is computed once and every branch is measured against it in the same process (no spike rasters cross a queue). Cons: while a fan computes (estimated 5–6 minutes on the full brain, below), ghosts wait.
2. **One job per branch.** Pros: ghosts can interleave between branches. Cons: each job must re-run from the checkpoint to the moment, and recompute or ship the untouched future's raster (millions of spikes) to measure the Hamming distance.
3. **A third brain process for fans.** Pros: ghosts never wait. Cons: breaks the two-process rule.
4. **A batched engine (`[neurons × B]` state, ADR-0029).** About 1.4–2.2× cheaper per future, but a change to `tramlines/brain/` and its determinism proof; a separate, delegated optimisation for later.

**Where the spikes go**

1. **Uniformly among the driven input neurons, in an order drawn from a generator seeded by the moment** (chosen), as `scripts/divergence_study.py --pick driven` did for ADR-0032/0036. A refused spike is recorded with the engine's reason and the next candidate is tried.
2. **One spike per sense** (sugar, bitter, looming, walking drive). Easier to read, but the senses differ hugely in size (the walking drive has 4 neurons), and it departs from the measured studies.

**When the button is offered**

1. **While a sense other than the walking drive receives input** (chosen): the fly is on food, bitter or laced food, or a shadow is growing. This is computed from the arena and the live poses on the server (`tramlines/server/fans.py`), sent to the viewer as `decisions`, and checked again when a request arrives.
2. **Only at the decision dish's two calibrated moments** (laced food, the faint shadow). Narrower; it would hide the button on the default dish entirely, although ADR-0029 found aimed spikes diverge there too while feeding (4/16).

## Decision
**Computing a fan** (`tramlines/timeline/branches.py`, pure and tested; run by the ghost worker, `tramlines/server/workers.py`):

- From the checkpoint behind the asked moment, the timeline runs untouched to that moment, so the spikes are added exactly at the playhead the viewer pressed at, not up to a second earlier.
- `aim`: the driven input neurons (`senses.rates_hz > 0`) in a `torch.randperm` order seeded by the moment in ms. Each candidate gets its own fork and `Brain.inject_spike`; a refusal (refractory, or fired at that very step) is kept with its reason and the next candidate is used, until 8 branches or the candidates run out. Choosing uses its own generator, so it changes no future.
- `run_untouched` forks once more and runs H with spike recording; `run_branch` runs each branch and measures it against it.

**Measures**, per branch:

| Measure | Definition |
|---|---|
| Path distance | distance between the two flies every ms (`divergence.path_distance_mm`) |
| Spike-raster Hamming distance | spikes in one raster but not the other, per 100 ms (`divergence.spike_differences`) |
| Time to divergence | first ms after the spike with the flies > 0.1 mm apart (ADR-0029's ε, Result 1's 0.1 mm) |
| Body re-converged | split, then within 0.1 mm **and** in the same feeding state at the horizon |
| Brain re-converged | at the horizon, `brain_difference(...).below(1e-9 mV)`: Result 4's ε ([ADR-0041](0041-result-4-backward-horizon.md)), on the full state (voltages, inputs, spikes in transit, refractory flags, random stream), not on spikes alone (the correction to ADR-0036) |
| Events | when each fly starts or stops feeding, and jumps |

**The untouched future is checked against the live fly**, bit for bit, as the live run arrives: two separate computations (projector and ghost process) of the same future must agree. The panel shows the count, e.g. "3,000 / 3,000 ms identical".

**Server** (`tramlines/server/app.py`, `fans.py`, `jobs.py`, `protocol.py`): viewer message `free_will` (`at_ms ≥ 1`), validated together with `choose` as one discriminated union; malformed messages are ignored. A request at a moment that is not a decision moment, or with no checkpoint behind it, is answered to the asking viewer alone with a fan marked `not_made` and the reason; nothing is queued. Otherwise the fan goes first in the ghost's queue, latest request first; a repeated request is not queued twice. Messages: `decisions`, `fan` (moment, decision, driven count, aimed and refused spikes with labels and reasons, the untouched future, its live check, done or not made), `branch` (one per future). `status.fans_to_compute` counts waiting fans. A missing checkpoint makes the fan `not_made`, never a fake.

**Labels.** Each spike is named by its sense, cell type and FlyWire root ID (v783 annotations), e.g. "sugar taste · ⟨cell type⟩ · ⟨root ID⟩", so where the spike went can be looked up in FlyWire Codex (ADR-0031's consequence).

**Caching and the log.** Each fan is written to `data/projections/<run key>_fan-t<ms>-<fan key>.json` when finished. The run key already fingerprints the code, the model's numbers, the data, the seed and the horizon; the fan key hashes the branch count, the aim rule, both ε and the bin width. The file is the fan's log: every aimed and refused spike, the untouched future and every branch. Fans are reloaded with the cached run and re-checked against it.

**On screen** (`web/`):
- **FREE WILL** (electric cyan, the one accent, ADR-0034) is enabled only at decision moments, with a soft glow; elsewhere its tooltip says why it is not offered.
- **The fan** on the arena: the untouched future as a thin gold line; each branch leaves the fork point gold and turns to its own hue as it moves 0 → 0.5 mm from the untouched fly, so the fan opens like light through a prism. Each branch unfolds over 4 s from when it arrives (eased; nothing bounces); with `prefers-reduced-motion` it is drawn at once. Each end is **filled** if the fly split for good, **hollow** if it never split or came back, with the branch's number beside it.
- **The free-will panel** (first in the side column while open): the moment and what is being decided; how many neurons were receiving input; refusals and their reasons; the live check of the untouched future; then one row per branch: number and swatch, the neuron, what the fly did ("split at 134 ms · 13.66 mm apart at the end · feeds at +0.62 s"), whether the brain forgot the spike, and a bar row of the spike differences per 100 ms (log scale shared by the fan; "·" is exactly none; exact numbers in its tooltip).
- **Footer** (CLAUDE.md 9.3): "branches: 8 · apart ▁▂▃▅▇", how many futures are more than 0.1 mm from the untouched one at each tenth of the horizon.
- A link can open a fan: `?t=1200&fan=1200`.

**Branch hues** (`--branch-1` … `--branch-8` in `tokens.css`): prism order (hue 25° → 340°), OKLCH chroma 0.11, lightness alternating 0.67 / 0.52. Checked with the dataviz palette validator on the viewer's surface `#07070a`: lightness band, chroma floor, contrast and adjacent-pair colour-blind and normal-vision separation all pass. Across *all* pairs some colour-blind pairs are close (worst ΔE 4.3), as expected for 8 overlapping series, so identity never rests on colour: every branch carries its number on the canvas and in the panel.

## Consequences
- **Cost (estimated, not measured on the full brain;** the perturbation atlas was running): about 9 runs of 3 s (8 branches + untouched) at ~35 s each (ADR-0038), plus up to 1 s of run-up: roughly 5–6 minutes per fan on one process. Measure it on the owner's machine before the gate run and record it in the journal.
- **Ghosts wait while a fan computes**, including the control's while the live run is still computing. The projector, which sets the playhead's lead, is not affected. A fan asked for by a viewer who has left still finishes and is cached.
- **The viewer's "decision moments" are wider than ADR-0032's two calibrated close calls**: any moment a taste or the shadow is active. At full-strength food the effect is weaker (ADR-0029: 4/16 diverged while feeding). The panel reports what happened rather than promising a split.
- **Small departures are sub-pixel.** At the arena's scale, 0.1 mm is less than a pixel; the numbers in the panel carry what the drawing cannot.
- **One fan is one moment of one run.** The rate at which spikes change behaviour, where and when, is Result 3's question; the honesty page says so.
- **Local only**, like `choose` (ADR-0042): any connected viewer can start a fan. A public server would need limits, or precomputed fans (owner decision 19).
- Tests on the 400-neuron network (`tests/test_free_will.py`): aiming (different driven neurons, the spike really in transit, repeatable, the moment untouched, a just-fired neuron refused and replaced); the untouched future equal to the moment run on; every measure against a separate run; re-convergence rules; decision moments; message validation; the worker's streamed fan equal to the library's, its untouched future equal to the projector's live poses; scheduling, the live check, caching and replay; refusal over the WebSocket. Small-network determinism gate rerun at 10 repeats (422/422).

## For learners
A deterministic program has one future. To see others, we copy the present eight times and change each copy by exactly one spike, in a neuron the world is stimulating right now, because that is where this model lets one spike matter. Then we run all nine futures and measure how far apart they drift: where the flies go, how many spikes differ, and whether each brain eventually forgets the extra spike. Often the brain forgets and the body does not. The screen names every neuron we touched, because a "choice" we injected ourselves should never be dressed up as the fly's.
