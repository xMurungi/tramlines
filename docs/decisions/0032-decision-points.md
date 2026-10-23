# 0032 — Decision points: where one spike can change what the fly does

- Status: Accepted (owner-delegated: "do what's best for the mission"; follows the owner-approved [ADR-0031](0031-proposal-aimed-free-will.md))
- Date: 2026-10-23
- Phase: 3 (for Phases 4–5)
- Decider: Claude (owner-delegated)

## Context
ADR-0031 aims the free-will spike at neurons receiving input, at *decision moments*. The divergence study ([ADR-0029](0029-divergence-batching-monitoring.md)) showed this model only lets a spike matter when the brain sits near one of the decoder's thresholds. So the arena needs moments built to be close calls.

## Options considered
1. **Graded stimuli calibrated to the thresholds:** give patches and shadows a `strength` that scales their port's rate, and find, by measurement, the strength at which the decision is a coin-flip across seeds.
2. **Change the decoder's thresholds instead.** Fewer moving parts, but it would change how the fly behaves everywhere, not only at the chosen moments.
3. **Random arenas**, hoping close calls occur. Unreliable, and uncheckable.

## Decision
Option 1.

- `Patch.strength` and `Loom.strength` (default 1.0: every existing run is unchanged) scale the port's rate in `senses.py`.
- `scripts/calibrate_decisions.py` sweeps strengths over 6 seeds with the walking drive on:

| Close call | Strength swept | Edge found | Chosen |
|---|---|---|---|
| **Laced food** (sugar plus bitter at strength s): does MN9 cross 30 Hz, "start feeding"? | 0.3 – 0.9 | 0.70 → 3/6 seeds feed; 0.80 → 1/6 | **0.72** |
| **Faint shadow** (looming input × s): does the Giant Fiber cross 50 Hz, "jump"? | 0.01 – 0.5 | 0.03 → 0/6 jump; 0.05 → 5/6 | **0.04** |

- `DECISION_ARENA` puts both on the fly's path: laced food at the food patch (reached at about 1.2 s), a faint shadow at 3.0–3.5 s. `DEFAULT_ARENA` is unchanged.

## What one aimed spike does there (`scripts/divergence_study.py --arena decision --pick driven`)

| Moment | Paths diverged | What the fly does differently |
|---|---|---|
| On laced food, 1.3 s | **15 / 16**, from 134 ms; up to 13.7 mm apart at 3 s | **In 6 of 16 futures it stops to feed**; the untouched fly walks across |
| Shadow growing, 3.3 s | **16 / 16**, but 15 of them follow *one* identical alternative path (6–9.6 mm from the untouched one) | Their brains still differ by about 14,360 spikes each: many brain futures, one behaviour |
| Shadow near its peak, 3.4 s | 6 / 16 | **In 1 of 16 the fly escapes** (jumps at 3.46 s, ends 17 mm away); the untouched fly stays |

The shadow's edge is one spike wide. The Giant Fiber fires 2 or 3 times in a 50 ms window (40 Hz vs 60 Hz around the 50 Hz threshold), so the outcome flips back and forth as the strength changes.

## Consequences
- **Free will is offered at these moments** (ADR-0031): stepping onto laced food, and a shadow approaching. Elsewhere the button would show near-nothing, and the viewer should say so rather than pretend.
- **The fan has structure:** futures that split widely (laced food), futures that collapse onto a few behaviours (3.3 s), and rare flips with large consequences (3.4 s). That variety is the experience CLAUDE.md 1.1 describes ("some collapse back together; some never do").
- Calibrated strengths depend on the model, senses and decoder; any change to those means re-running `calibrate_decisions.py`.
- Data: `docs/assets/divergence_decision_driven_*.csv`; fans: `docs/assets/fan_decision_driven_*.png`.
- **Machine rule tightened:** with 3 workers, memory pressure reached macOS's "warning" level twice (39% available; other apps open). Every script now defaults to **2 parallel brain processes** (amends the 3-process rule of ADR-0029).
- The laced-food result was run three times with identical numbers (15/16 diverged, 6 fed, 13.66 mm maximum).

## For learners
A coin balanced on its edge falls one way or the other from the slightest touch. We looked for the edges in the fly's world, where its brain is nearly half one way and half the other, and placed them on its path. There, and almost only there, a single extra spike changes what the fly does.
