# 0024 — Proposal: how brain activity becomes movement

- Status: Superseded by [0028](0028-senses-and-decoder-chosen.md) (owner delegated the choice, 2026-10-22). Kept unchanged below as the record of the options.
- Date: 2026-10-22
- Phase: 3
- Decider: Owner (CLAUDE.md 2.2 and 8.2: Reserved)

## Context
FlyWire is a brain without a body. Descending neurons carry the brain's commands to the nerve cord, which we do not have. The decoder reads their firing rates and turns them into movement in the 2D world. It must be pure and deterministic: the same rates in always give the same movement out. All gains and thresholds will live in `tramlines/world/decoder.py`. Evidence comes from the port survey in [ADR-0023](0023-proposal-sensory-ports.md).

## Readout neurons found in the v783 annotations (release v2.1.0)

| Movement | CLAUDE.md 8.2 suggests | Found as | Neurons | Responds in the survey? |
|---|---|---|---|---|
| Forward speed | P9 and BPN | P9 = `hemibrain_type DNp09` (matches Eon's P9 IDs) | 4 (2 per side) | Only when driven directly, or slightly by right-side LPLC2 |
| | | BPN | **not found** under that name in v2.1.0 or v3.2.0 | — |
| Turning | DNa02 (and DNa01) left − right | DNa02 = `hemibrain_type DNa02`; DNa01 = `cell_type DNa01` | 2 + 2 | DNa02 yes (loom, P9 drive); DNa01 never |
| Backward | MDN | `hemibrain_type MDN` (cell type DNp50) | 4 | Barely (≤ 4 Hz) |
| Escape jump | Giant Fiber | `hemibrain_type Giant Fiber` (cell type DNp01) | 2 | Strongly, to looming |
| Feeding | MN9 | `cell_type CB0701` (reference MN9 and its partner) | 2 | Strongly, to sugar |

## Proposed decoder
Rates are counted over a sliding **50 ms window**, updated every 1 ms of simulated time ([ADR-0025](0025-world-and-timeline.md)).

- **Forward speed** = `gain_fwd × mean(P9 rate)`, capped at 30 mm/s (real flies walk at about 10–20 mm/s).
- **Turning rate** = `gain_turn × (DNa02 left − DNa02 right)`; the sign convention (which side turns which way) needs a literature check (Rayshubskiy et al. 2020) before approval.
- **Backward** = `gain_back × mean(MDN rate)`, subtracted from forward speed.
- **Escape jump** when the Giant Fiber rate passes a threshold (e.g. 50 Hz): an instant hop of a few millimetres away from the threat, then a short cooldown.
- **Feeding** when MN9 (either side) passes a threshold (e.g. 30 Hz): the fly stops and extends its proboscis.

**Calibrating the gains:** choose each so that the rates seen in the survey map to realistic movement: P9 at about 140 Hz → about 15 mm/s; a DNa02 difference of 40 Hz → about 180°/s. Each constant gets one line of justification in `decoder.py`.

## Options considered
1. **Rate-based linear decoder with thresholds for discrete actions (above).** Simple, explainable in one chapter, deterministic.
2. **A trained decoder** (fit to real fly walking data). More realistic, but needs datasets we do not have, and hides the mapping.
3. **Population vector of all descending neurons.** More "brain-wide", but no literature anchor, and hard to explain honestly.

## Open questions for the owner
1. Approve option 1, and the readout table above?
2. BPN cannot be found by name: proceed with P9 alone for forward speed?
3. MDN barely fires to any stimulus tested: keep backward walking (it will rarely happen), or drop it?
4. Jump behaviour: distance and direction (away from the threat, or straight ahead)?

## Consequences
- Most of the fly's visible "behaviour" will come from these few constants and from the walking drive (ADR-0023 port 5). The honesty page will say so.
- Turning depends on two neurons; if they rarely differ, the fly will walk mostly straight. The Phase 3 gate (a trajectory showing purposeful behaviour) will show whether that is enough.

## For learners
A brain's commands leave through a narrow channel: a few hundred descending neurons. We listen to a handful whose job scientists have studied, and translate their firing into speed, turning, jumping and feeding. The translation is ours, not the fly's. Chapter 26 shows exactly where the line falls.
