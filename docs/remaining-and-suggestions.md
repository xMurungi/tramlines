# What remains, and suggestions

Written 2026-10-24 (session 9), while Result 4's study was running. Sizes are in working sessions like session 9 and are estimates, not promises. The live checklist is [`ROADMAP.md`](https://github.com/xMurungi/tramlines/blob/develop/ROADMAP.md); decisions only the owner can make are on the [owner decisions](owner-decisions.md) page.

## Where the project stands

| | Status |
|---|---|
| Phases 0–3 (data, engine, determinism, body and world) | Done, gates passed |
| Phase 4 (ghost and viewer) | Built and watched; formal sign-off is owner decision 15 |
| Result 1, predictability horizon | Done: two passes, corrected once ([ADR-0037](decisions/0037-result-1-predictability-horizon.md), [ADR-0038](decisions/0038-result-1-second-pass.md)) |
| Result 2, null brain | Done: full and partial rewiring, decoder-free check ([ADR-0039](decisions/0039-result-2-null-brain.md)) |
| Result 4, backward horizon | Done, pre-registered: the brain forgets, the body remembers ([ADR-0041](decisions/0041-result-4-backward-horizon.md)) |
| Result 3, perturbation atlas | Not started |

The science is about half done; presenting it and writing it up are mostly still ahead.

## Remaining work

### Phase 5: the demon's limits
1. ~~Finish Result 4~~ (done, [ADR-0041](decisions/0041-result-4-backward-horizon.md)).
2. **Result 3, the perturbation atlas** (1–2 sessions, several hours of computing). Single extra spikes swept across neurons and moments, screened cheaply at the spike level, behaviour simulated only for cascades. Report the fraction that change behaviour, and where and when. Then check that the tipping points survive decoder changes (100 ms window, thresholds ±20%). Pre-register it like Result 4.
3. **Viewer** (1–2 sessions): the knowledge slider (Result 1); the perfect ghost labelled as the control; the aimed free-will fan; replay, which can now also show Result 4 ("two pasts, one present").
4. **Gate (owner):** a stranger understands it in 30 seconds.

### Phase 6: polish and launch preparation (2–3 sessions)
- Aesthetic pass, honesty page, about page with credits, performance budget, mobile layout.
- The launch clip script (owner approves).
- **The long-form write-up of the four results**, with data and scripts, after a literature check (London et al. 2010; van Vreeswijk & Sompolinsky 1996; Landauer 1961; work on connectome-constrained models and their robustness).

Before recording the clip: freeze the code, then run `uv run python -m tramlines.server.precompute` (about 4–5 hours) so every slider setting plays instantly (owner decision 25).

### Phase 7: into the browser (1–2 sessions, if decision 19 is approved)
Precomputed runs plus a browser player, rather than a live engine (WebGPU has no 64-bit floats).

### Phase 8: release (owner)
Licence, name, launch channels and timing.

**Total:** about 7–11 sessions of building, plus owner decisions and gates. Not included: Book chapters (decision 20) and the connectome-error study (decision 22), a few sessions each.

## Decisions waiting for the owner
In rough order of what they unblock:

| # | Decision | Blocks |
|---|---|---|
| 15 | Phase 4 sign-off (watch 60 s; already cached) | Formally closing Phase 4 |
| 19 | Phase 7 as precomputed runs + browser player | Phase 7 |
| 20 | The Book's scope | How much writing goes into chapters |
| 12 | Continuous integration on GitHub | Automatic checks on every PR |
| 22 | How accurate must a connectome be? (follow-up study) | Nothing now |
| 7, 6, 10 | Licence, name, launch | Phase 8 (and whether code can be borrowed from GPL projects) |
| 1–5, 9 | Older acknowledgements (model details, sugar neurons, annotation source, speed, file names, defaults) | Nothing; the builder's defaults are in use |

## Suggestions

### To raise the science to the standard of a serious paper
1. **Pre-register every remaining result.** Result 4 set the pattern: merge the analysis plan, with numeric criteria, before running. Do the same for Result 3.
2. **Uncertainty everywhere.** Results 1 and 2 report counts; recompute them with Wilson intervals and bootstrap medians (the Result 4 analysis code does this already) before the write-up.
3. **Robustness to the model's own assumptions,** following Shiu et al. 2024's checks: rerun headline results with w_syn ±30% and with glutamate treated as excitatory (which, in their model, removes bitter's inhibition of feeding, so our laced-food decision should depend on it). See [literature notes](science/literature-notes.md).
3b. **Replicate the key numbers independently.** The engine already matches Brian2 spike for spike; rerun one headline case of each result through Brian2 (or the reference code) to show it isn't our engine.
4. **Strengthen Result 2.** (a) A second null that keeps each neuron's balance of excitation and inhibition; it would test whether the runaway activity in partly rewired brains comes from losing that balance. (b) More null brains per rewiring level (5–10, not 3).
5. **The question a connectome lab would read (decision 22).** Replace random rewiring with realistic connectome errors: missed synapses at measured detection rates, wrong neurotransmitter predictions at measured error rates, merge and split errors. Ask which behaviours each kind of error breaks first. Result 2 suggests multi-sense decisions (the bitter veto) are the most fragile. That's a concrete, useful claim for anyone building models from connectomes, Shiu et al. included.
6. **Treat the write-up as a paper from now on.** One figure per result; a methods section built from the ADRs; data and scripts released together; limitations stated as plainly as the ADRs state them. Check novelty in the literature before claiming any.
7. **Ask experts only once the write-up is solid.** Feedback from the people whose model we build on (Shiu et al., the FlyWire team) would be the strongest test. Contacting anyone is outward-facing and the owner's call; do it after the literature check, with the honesty page linked.

### To keep the engineering trustworthy
8. **Continuous integration (decision 12).** The missed-spike bug lived for two results; automatic tests on every PR, plus a rule that perturbations fail loudly, make that kind of bug harder to miss.
9. **Memory discipline.** The decoder-free run pushed swap to about 4 GB. Runs of rewired or runaway brains should start on 1 worker, or the script should drop to 1 when memory pressure reaches "warning".
10. **A shared measurement library.** Studies still repeat code (loading moments, running pairs, writing CSVs). Moving it into `tramlines/timeline/` with tests, as `brain_difference` now is, cuts bugs and makes each new study shorter.

### To make the experience land
11. **Lead the viewer with one sentence per result,** each with its picture: "the ghost needs every spike, not every decimal"; "the behaviour lives in the wiring, and survives a lot of damage"; "the brain forgets, the body remembers".
12. **Use Result 4 for replay:** show two different pasts arriving at the same present brain while the flies stand in different places.
13. **Keep the honesty page in step with every result.** Each new claim gets its caveat on the same day.
