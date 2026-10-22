# Decisions waiting for the owner

This page lists every decision only the owner can make, so it can be picked up at any time. Each item has a recommendation and says what it blocks. Answer in any session ("decision 3: yes") and the builder records the answer in the linked ADR and moves the item to *Answered*.

Last updated: 2026-10-22 (session 3).

## Waiting

| # | Decision | Recommendation | Blocks | Details |
|---|---|---|---|---|
| 1 | **Acknowledge the model details where the reference code differs from CLAUDE.md 7.2**, and say whether CLAUDE.md 7.2 should be rewritten to match. | Acknowledge, and update 7.2 to the verified model in ADR-0016. The engine already follows the reference code, as 7.2 instructs. | Nothing today. A wrong 7.2 will mislead future sessions and Book readers. | [ADR-0014](decisions/0014-challenge-reference-model-details.md), [ADR-0016](decisions/0016-verified-neuron-model.md) |
| 2 | **Which sugar neurons count as "the fly tasting sugar"** in the world (Phase 3 sensory port). Options: the 21 used by the reference experiment, or all 67 `sugar/water` neurons on that side (which include water-sensing cells). | Keep the reference 21 for the scientific test (already done). Decide the Phase 3 port once the Phase 3 proposal is written. | Phase 3 only. | [ADR-0017](decisions/0017-annotations-and-neuron-sets.md) |
| 3 | **Annotation source.** CLAUDE.md 7.1 says annotations come from FlyWire Codex. Codex downloads need a login, so we use the published release behind Codex: `flywire_annotations` v2.1.0 (2024), the release that matches v783 exactly. | Accept v2.1.0. | Nothing; reversible. | [ADR-0017](decisions/0017-annotations-and-neuron-sets.md) |
| 4 | **Speed.** The brain runs at 0.1× real time (about 10 s of computer time per simulated second, single-threaded, float64). Phase 4 needs at least 1×. Options will come as an ADR in Phase 2–4. Changing language is yours to decide. | Nothing to decide yet. The likely options (fewer per-step operations, batching, a compiled kernel) stay within PyTorch. | Phase 4. | [ADR-0018](decisions/0018-event-driven-engine.md) |
| 5 | **Data file names.** CLAUDE.md 7.1 expects Eon's `2025_…` names; we keep the original `Completeness_783.csv` / `Connectivity_783.parquet` (same content). | Keep upstream names. | Nothing. | [ADR-0013](decisions/0013-data-files-and-source.md) |
| 6 | **Project name.** "Tramlines" is a working title. | (Yours.) | Phase 8. | CLAUDE.md 17.1 |
| 7 | **Code licence** (MIT / Apache-2.0 / GPL-3.0). Note: Eon's code is GPL-2.0-or-later, so we do not copy from it until this is decided. Shiu's code is MIT. | (Yours.) | Phase 8; also whether we may reuse Eon code. | CLAUDE.md 17.2 |
| 8 | **Go for Phase 3, and approve the sensory ports (8.1) and motor decoder (8.2).** Phase 2 is done; Phase 3 cannot start building the world's senses or movement without these. | Say "go"; the builder then writes the two proposal ADRs and stops for your approval before implementing them. | **Phase 3 (next).** | CLAUDE.md 8, 10 |
| 9 | **Default prediction horizon (3 s) and branch count (8).** | Keep the defaults until the performance numbers for Phase 4 exist. | Phase 4–5. | CLAUDE.md 17.4 |
| 10 | **Launch channels and timing.** | (Yours.) | Phase 8. | CLAUDE.md 17.5 |

## Answered

| # | Decision | Answer | Date |
|---|---|---|---|
| — | Go for Phase 1 | Go. | 2026-10-22 |
| — | Go for Phase 2 | Go; other decisions deferred until later. | 2026-10-22 |
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

Everything the builder installed, downloaded or contacted is listed on [sources and access](sources-and-access.md).
