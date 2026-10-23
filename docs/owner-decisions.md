# Decisions waiting for the owner

This page lists every decision only the owner can make, so it can be picked up at any time. Each item has a recommendation and says what it blocks. Answer in any session ("decision 3: yes") and the builder records the answer in the linked ADR and moves the item to *Answered*.

Last updated: 2026-10-23 (session 7, after the review in issue #14). Every choice made so far, in order: [decision history](decisions/history.md).

## Waiting

| # | Decision | Recommendation | Blocks | Details |
|---|---|---|---|---|
| 16 | **Reframe the project as "an honest Laplace's demon"** (from the review in issue #14): the perfect ghost becomes the openly labelled control; v1.0 becomes three measured results (predictability horizon, the brain's contribution against a null brain, a perturbation atlas), the viewer with a knowledge slider, and a write-up. | Adopt. It makes the Devs moment earned instead of a trick, and gives the project an end. | Phase 5 onward, and CLAUDE.md 1.1 / 1.3. | [ADR-0035](decisions/0035-proposal-honest-laplaces-demon.md) |
| 17 | **Inputs and readouts must not overlap:** today P9 is both driven and read for speed. Choose a new walking drive or speed readout. | Drive walking upstream of P9 (to be surveyed), keep P9 as readout; add a test that the sets never overlap. | Honest speed; part of 16. | [ADR-0035](decisions/0035-proposal-honest-laplaces-demon.md) |
| 18 | **Issues #11–#13** are the raw pasted conversation behind #14; they repeat it and contain a path with part of your name and your work machine's folder layout. | Close them as duplicates of #14 and edit out the paths (the builder can do this on your go). | Nothing; privacy. | GitHub issues |
| 15 | **Phase 4 gate: watch the ghost lead and the fly follow for 60 s.** Already computed and cached, so it plays instantly: `cd web && npm install && npm run build`, then `uv run python -m tramlines.server`, then open http://127.0.0.1:8000. | Watch; say whether it passes. | Phase 5 (free will in the viewer). | [ADR-0033](decisions/0033-phase-4-architecture.md) |
| 1 | **Acknowledge the model details where the reference code differs from CLAUDE.md 7.2**, and say whether CLAUDE.md 7.2 should be rewritten to match. | Acknowledge, and update 7.2 to the verified model in ADR-0016. The engine already follows the reference code, as 7.2 instructs. | Nothing today. A wrong 7.2 will mislead future sessions and Book readers. | [ADR-0014](decisions/0014-challenge-reference-model-details.md), [ADR-0016](decisions/0016-verified-neuron-model.md) |
| 2 | **Which sugar neurons count as "the fly tasting sugar"** in the world (Phase 3 sensory port). Options: the 21 used by the reference experiment, or all 67 `sugar/water` neurons on that side (which include water-sensing cells). | Keep the reference 21 for the scientific test (already done). Decide the Phase 3 port once the Phase 3 proposal is written. | Phase 3 only. | [ADR-0017](decisions/0017-annotations-and-neuron-sets.md) |
| 3 | **Annotation source.** CLAUDE.md 7.1 says annotations come from FlyWire Codex. Codex downloads need a login, so we use the published release behind Codex: `flywire_annotations` v2.1.0 (2024), the release that matches v783 exactly. | Accept v2.1.0. | Nothing; reversible. | [ADR-0017](decisions/0017-annotations-and-neuron-sets.md) |
| 4 | **Speed.** Closed-loop fly at 0.12× real time. With projection-not-live ([ADR-0030](decisions/0030-projection-not-live.md)) a compiled kernel is no longer needed for Phase 4; it would only shorten preparation and branch waits. | Defer. | Nothing now. | [ADR-0027](decisions/0027-awake-set-engine.md), [ADR-0030](decisions/0030-projection-not-live.md) |
| 5 | **Data file names.** CLAUDE.md 7.1 expects Eon's `2025_…` names; we keep the original `Completeness_783.csv` / `Connectivity_783.parquet` (same content). | Keep upstream names. | Nothing. | [ADR-0013](decisions/0013-data-files-and-source.md) |
| 6 | **Project name.** "Tramlines" is a working title. | (Yours.) | Phase 8. | CLAUDE.md 17.1 |
| 7 | **Code licence** (MIT / Apache-2.0 / GPL-3.0). Note: Eon's code is GPL-2.0-or-later, so we do not copy from it until this is decided. Shiu's code is MIT. | (Yours.) | Phase 8; also whether we may reuse Eon code. | CLAUDE.md 17.2 |
| 9 | **Default prediction horizon (3 s) and branch count (8).** | Keep the defaults until the performance numbers for Phase 4 exist. | Phase 4–5. | CLAUDE.md 17.4 |
| 10 | **Launch channels and timing.** | (Yours.) | Phase 8. | CLAUDE.md 17.5 |
| 12 | **Continuous integration on GitHub** (GitHub Actions running the tests on every PR). Today checks run locally and are recorded in each PR. | Add it: tests, lint, types and docs on every PR; data-dependent tests skip on GitHub unless the data is cached there. | Nothing; makes PR checks visible. | [ADR-0026](decisions/0026-branches-and-pull-requests.md) |

## Answered

| # | Decision | Answer | Date |
|---|---|---|---|
| — | Go for Phase 1 | Go. | 2026-10-22 |
| — | Go for Phase 2 | Go; other decisions deferred until later. | 2026-10-22 |
| — | Go for Phase 3 | Go; decisions deferred. | 2026-10-22 |
| — | Workflow | Pull requests, merged into `develop` ([ADR-0026](decisions/0026-branches-and-pull-requests.md)). | 2026-10-22 |
| — | Phase 3 gate and Phase 4 | "Proceed partner" (after the builder asked for the Phase 3 verdict and a go for Phase 4), taken as both. Say so if that was not meant. | 2026-10-23 |
| 13 | Free will: aim the extra spike | Approved: option 2, aimed at driven inputs, at decision moments ([ADR-0031](decisions/0031-proposal-aimed-free-will.md)). | 2026-10-23 |
| 14 | Projection, not live; amend CLAUDE.md | Approved ([ADR-0030](decisions/0030-projection-not-live.md)); CLAUDE.md Phases 4, 5 and 13.3 amended. | 2026-10-23 |
| 8, 11 | Sensory ports and motor decoder | Delegated: "choose what's best and let's see how it goes; keep a history". Chosen in [ADR-0028](decisions/0028-senses-and-decoder-chosen.md); history in [decision history](decisions/history.md). You can still change any of it. | 2026-10-22 |
| — | Privacy | Only the GitHub handle `xMurungi` appears anywhere public; no name, device or local paths. History rewritten accordingly. | 2026-10-22 |
| — | Git remote | Push to `github.com/xMurungi/tramlines`, branch `develop`. | 2026-10-22 |
| — | Machine for the performance budget (CLAUDE.md 17.6) | The machine used in these sessions (specs kept private, not in the repository). | 2026-10-22 |

## Decided by the builder (delegated; you may overrule any)

These were in the builder's remit and are recorded as ADRs. Listed here so nothing surprises you.

- [ADR-0013](decisions/0013-data-files-and-source.md): download source for the v783 files (Shiu repository, pinned commit).
- [ADR-0015](decisions/0015-test-conventions.md): test conventions.
- [ADR-0016](decisions/0016-verified-neuron-model.md): the neuron model as verified against Brian2, spike for spike.
- [ADR-0017](decisions/0017-annotations-and-neuron-sets.md): annotation release and the neurons used for the sugar → MN9 test.
- [ADR-0018](decisions/0018-event-driven-engine.md): engine design (event-driven spike delivery).
- [ADR-0019](decisions/0019-plotting.md): matplotlib for figures, in an optional `analysis` dependency group.
- [ADR-0020](decisions/0020-sugar-mn9-regression-bands.md): tolerance bands for the sugar → MN9 regression test.
- [ADR-0021](decisions/0021-brain-state-fork-save.md): what the brain state contains, how forks and saved files work.
- [ADR-0022](decisions/0022-determinism-test-protocol.md): how the sacred tests define and prove "identical".
- [ADR-0025](decisions/0025-world-and-timeline.md): the arena, the fly's body, the 1 ms world step and the timeline loop.
- [ADR-0027](decisions/0027-awake-set-engine.md): the faster engine (only awake neurons computed; identical results).

Everything the builder installed, downloaded or contacted is listed on [sources and access](sources-and-access.md).
