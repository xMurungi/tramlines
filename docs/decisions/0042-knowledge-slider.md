# 0042 — The knowledge slider: the control, and ghosts that know less

- Status: Accepted (delegated)
- Date: 2026-10-24
- Phase: 5
- Decider: Claude (delegated, within ADR-0033's architecture and the owner-adopted ADR-0035)

## Context
ADR-0035 makes the perfect ghost the **control**: a bit-exact copy is always right because the simulation is deterministic, and that is copying, not predicting. The viewer's question becomes "how much does the ghost know?" Result 1 ([ADR-0037](0037-result-1-predictability-horizon.md), [ADR-0038](0038-result-1-second-pass.md)) measured which kinds of imperfect knowledge matter. This decision puts them on screen: a slider of knowledge settings, an imperfect ghost drawn peeling away from the live fly, and a match meter that shows the divergence honestly.

Constraints: keep ADR-0033's architecture (projector + independent ghost process, per-viewer outboxes, cache keys fingerprinted by everything that changes results); at most two brain processes ([ADR-0032](0032-decision-points.md)); "one missed spike" must never silently become a perfect copy ([ADR-0038](0038-result-1-second-pass.md), `NoSpikeInTransit`).

## Options considered
**Where imperfect ghosts are computed**

1. **The same ghost process, on demand, one job at a time** (chosen). The server keeps the job list and feeds the process the next job only when the last one is answered, so it can reorder: the setting a viewer chose most recently goes first, from the checkpoint behind that viewer's playhead, then wraps round. Pros: still two brain processes; what someone is watching is computed first. Cons: while the live run is still computing, a chosen setting competes with the control.
2. **A third brain process for imperfect ghosts.** Pros: the control never waits. Cons: breaks the two-process rule (ADR-0032) that kept memory pressure normal.
3. **Precompute every setting with every run.** Pros: the slider is instant from the first viewing. Cons: about 7 × 60 perturbed ghosts per 60 s run, roughly 4 hours on one process at ADR-0038's ~35 s per 3 s ghost, mostly for settings nobody chooses.

**The slider's form**

1. **A vertical track of native radio stops, most knowledge at the top** (chosen). Individual stops can be disabled (the missed spike at quiet moments), arrow keys skip disabled stops, and it fits the side panel on a phone.
2. **An `<input type="range">`.** A single control, but a stop cannot be disabled; moving onto an unavailable stop would have to snap back.

## Decision
**Settings** (`tramlines/server/knowledge.py`, sent to the viewer in `hello`, so the slider and the server never disagree), in order: everything (the control); float32; voltage known to 0.001, 0.01 and 0.1 mV; 99.9% and 99% of neurons observed; one in-flight spike missed. Within a kind the order is by size of error (float32's ~10⁻⁶ mV sits above 0.001 mV); kinds are not ranked against each other. Each uses draw 0 of its error (seed 0), the draw of the first pass.

**The ghost worker** (`tramlines/server/workers.py`) answers each job `(setting, checkpoint, file)`: it loads the checkpoint, applies `perturb.blur` for any setting but the control, and runs `H` ahead. Only the brain is blurred; the body, the arena and the brain's random-number stream are exact, so the only difference from the live fly is the knowledge error. If `blur` raises `NoSpikeInTransit`, the worker sends a **refusal** with the reason, never a ghost.

**Offering the missed spike.** The projector reports the number of spikes in transit at every checkpoint. The viewer disables "1 spike missed" while the checkpoint behind the playhead has none, and says why. The worker's refusal is the backstop, and the one source of truth.

**Checkpoints are kept** (in `data/projections/<run key>_checkpoints/`), reversing the deletion of issue #14 B5: a viewer may ask for another setting at the same moment later. If one is missing, the server refuses that ghost and says so.

**Scoring** (`tramlines/server/history.py`), one track per setting:
- *bit-exact*: milliseconds equal in every field, the control's test (ADR-0033);
- *on path*: milliseconds within 0.1 mm of the live fly, Result 1's test;
- *right for*: for each ghost, the milliseconds on path before its first miss (Result 1's convention), once its whole horizon has been checked.
As before, the viewer counts only seconds already watched (issue #14, B7).

**Protocol** (`tramlines/server/protocol.py`): new server messages `checkpoint` (moment, spikes in transit) and `refused`; `ghost` and `match` carry their setting; `status.to_compute` says how many ghosts each chosen setting still needs. One viewer message, `choose` (setting, playhead), validated; anything malformed is ignored.

**Caching.** The live run and its control keep their file, `<run key>.json`. Every other setting has its own file, `<run key>_<setting key>.json`, where the setting key hashes its kind, size and random draw; the run key already fingerprints the code, the model's numbers and the data (issue #14, B2). A setting's file is written once every checkpoint of the finished run has a ghost or a refusal.

**On screen** (`web/`):
- The prediction panel names the ghost: **THE CONTROL**, or *imperfect ghost · 0.1 mV*. The control's note says it is always right because the simulation is deterministic, and that this is copying, not predicting. Every ghost is also labelled on the canvas.
- An imperfect ghost is drawn from its checkpoint up to now against the live fly: on the path in ghost gold, off it in a new token `--ghost-off` (a muted rose), with a ring where it left the path and a faint ghost fly where it says the fly is now. Only moments already played are compared, so the screen never reveals the live fly's future.
- Meters: bit-exact %, on-path %, and "this ghost": *on path so far*, *peeled away after N ms*, *right for all 3.0 s*, *not made*, or *computing · N to go*.
- A link can open a setting at a moment: `?knowledge=voltage-0.1&t=1200`.

## Consequences
- **Cost (estimated, not yet measured on the full brain;** the backward-horizon study was running): one setting for a 60 s run is about 60 ghosts × ~35 s ≈ 35 minutes on one process; each is cached afterwards. Checkpoints take about 6 MB per simulated second (~360 MB for the 60 s gate run), kept until the cached run is deleted.
- **The control can wait.** While the live run is still computing, a viewer's choice comes first and the control's ghosts wait. The projector, which sets the playhead's lead, is not affected.
- **A choice outlives its viewer.** A setting chosen by a viewer who has left keeps computing to the end. The result is cached, so the work is not wasted.
- **Small departures are sub-pixel.** At the arena's scale, 0.1 mm is less than a pixel; the ring marks where a ghost left the path even when the two flies still overlap.
- **One draw per setting.** Result 1 shows outcomes differ between draws and seeds; the honesty page says what is on screen is one example, not a rate.
- **Local only.** `choose` lets any connected viewer start computing. That is fine on 127.0.0.1; a public server (Phase 7) would need limits, or precomputed runs (owner decision 19).
- Tested on the 400-neuron network: the worker's ghost equals the hand-blurred state run forward, for every setting; the missed spike is refused exactly at moments with no spike in transit; scheduling, scoring, caching and the WebSocket `choose` round trip (`tests/test_knowledge.py`).

## For learners
A machine that copies a deterministic brain exactly will always "predict" it: that is the control, and the screen says so. The real question is what happens when the copy is a little wrong, the way any measurement is. The slider lets you choose how wrong, from "rounded to single precision" to "missed one spike", and the ghost restarts from the blurred brain every second. Where it leaves the fly's path is where knowing less stopped being good enough. See [Chapter 22](../book/ch22-the-ghost.md).
