# 0023 — Proposal: which neurons are the fly's senses

- Status: Superseded by [0028](0028-senses-and-decoder-chosen.md) (owner delegated the choice, 2026-10-22). Kept unchanged below as the record of the options.
- Date: 2026-10-22
- Phase: 3
- Decider: Owner (CLAUDE.md 2.2: choosing sensory neurons is Reserved)

## Context
The 2D world has to reach the brain. Each world event is a *port*: a set of neurons, found by annotation, that receive Poisson input at a rate the world sets. CLAUDE.md 8.1 lists four candidate ports. Phase 3 measured how strongly each candidate drives the movement neurons ([ADR-0024](0024-proposal-motor-decoder.md)) before anything is decided. All neuron sets below come from the v783 annotations, release v2.1.0 ([ADR-0017](0017-annotations-and-neuron-sets.md)).

## Evidence: the port survey
Each stimulus at 150 Hz for 1 s, mean of 3 seeds, spikes per second in candidate movement neurons (`scripts/survey_ports.py`, data in `docs/assets/port_survey.csv`):

| Stimulus | P9 (DNp09) | DNa02 L / R | Giant Fiber L / R | MN9 L / R | MDN, DNa01 |
|---|---|---|---|---|---|
| none | 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 |
| sugar, 21 reference GRNs | 0 | 0 / 0 | 0 / 0 | **59 / 80** | 0 |
| bitter, 42 GRNs | 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 |
| loom right, LC4 (50) | 0 | 9 / 0 | **31 / 124** | 0 / 0 | ≤ 0.3 |
| loom right, LPLC2 (102) | 31 (one, right) | 44 / 0 | **99 / 158** | 0 / 0 | ≤ 4 |
| wind right, JO-C/E (206) | 0 | 0 / 0.3 | 0 / 0 | 0 / 0 | 0 |
| P9 driven directly (4) | 136–152 | 14 / 20 | 0 / 0 | 0 / 0 | 0 |

**The most important finding: with no input the whole brain is silent.** The model has no spontaneous activity, so the fly will not walk unless something drives it. That makes a fifth "port" necessary, and it is the most consequential choice here.

!!! note "Update, 2026-10-22: sugar + bitter check"
    Sugar GRNs held at 150 Hz while all 42 bitter GRNs are swept (`scripts/sugar_bitter.py`, 5 seeds, `docs/assets/sugar_bitter.csv`). MN9 right / left:

    | Bitter | 0 Hz | 50 Hz | 100 Hz | 150 Hz | 200 Hz |
    |---|---|---|---|---|---|
    | MN9 right (reference) | 84.6 | 53.4 | 10.8 | 0.2 | 0.2 |
    | MN9 left | 56.2 | 33.0 | 7.2 | 0.0 | 0.0 |

    Bitter suppresses sugar-evoked feeding, dose-dependently, and abolishes it at equal rates. This matches the qualitative result in Shiu et al. 2024 and confirms port 2's role.

## Options and recommendation, port by port

**1. Food → sugar GRNs.** *Recommended:* the 21 reference GRNs at 150 Hz while the fly stands on food (drives MN9 strongly, as in Phase 1). *Alternative:* all 67 `sugar/water` GRNs on that side (stronger, but includes water cells), or both sides' 131.

**2. Bitter patch → bitter GRNs.** *Recommended:* all 42 bitter GRNs (both sides) at 150 Hz. Alone they drive none of the movement neurons; their expected role is to suppress feeding when combined with sugar. This should be checked with a sugar + bitter run before approval.

**3. Looming shadow → visual projection neurons.** *Recommended:* LPLC2 on the side the shadow approaches from, with the rate rising as the shadow grows (0 → 200 Hz). It drives the Giant Fiber (the escape neuron) hard and on the correct side. *Alternative:* LC4 (weaker, more selective for the Giant Fiber), or both.

**4. Wall / touch → Johnston's organ.** *Recommended: drop or replace.* Wind-sensitive JO neurons drove nothing measurable. Options: (a) no touch port, walls simply stop the fly; (b) try mechanosensory bristle neurons (another survey first).

**5. Walking drive (new, needed).** Without it the fly stands still forever. Options:
   - (a) **Tonic drive to P9 (DNp09, 4 neurons)** at a fixed rate, e.g. 60–100 Hz. Simple and honest to state: "we tell the fly to walk; its brain decides where". *Recommended*, with the honesty page saying so.
   - (b) Low-rate background noise into many sensory neurons, hoping walking emerges. More "natural" sounding, but unvalidated, and it changes the published model's assumptions.
   - (c) No drive: the fly only moves when stimulated (escape jumps, feeding). Least invented, but nearly static.

## Consequences
- Whatever is chosen, the honesty page must name every port and its rates.
- Once approved, the ports go into `tramlines/world/senses.py`, each one citing this ADR.
- All stimulated neurons get the reference model's zero refractory period. Changing a port set therefore changes the brain's input set, and saved states from before the change cannot be loaded into a brain after it.

## For learners
A real fly's senses are millions of receptors. Ours are a handful of switches, each wired to a group of neurons that scientists have identified. Choosing those switches is where our design enters the fly's world, so we measure before we choose, and we write the choice down. Chapter 26 is about exactly this.
