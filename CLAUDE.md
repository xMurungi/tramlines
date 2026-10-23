# CLAUDE.md — Project TRAMLINES

> *A real fly's brain, copied synapse by synapse, running in a machine that can see its future.*

This file is the constitution of this repository. Read it **in full** at the start of every session before touching code. It tells you what we are building, why, how, in what order, what has already been decided, what you may decide yourself, and what you must never decide without the owner.

Owner and sole authority: **xMurungi** (referred to below as "the owner").

---

## 0. How to use this file

1. Read sections 1–4 every session. They do not change often and they define the soul of the project.
2. Check `docs/journal/` (latest entry) and `ROADMAP.md` to see where the last session stopped.
3. Work only on the current phase (section 10). Do not jump ahead.
4. Every non-trivial choice you make becomes an ADR (section 5).
5. Every piece of code you write gets its chapter (or chapter update) in The Book (section 12).
6. End every session with a journal entry (section 13.4).

If anything in this file conflicts with a request in a session, **stop and ask the owner**. Do not resolve the conflict yourself.

---

## 1. The mission

### 1.1 What we are building

> **Reframed 2026-10-23 (ADR-0035, adopted by the owner): an honest Laplace's demon.** The original Devs-demo concept is preserved at git tag `v0.4.0`.

**Tramlines** is a whole-brain emulation of the adult fruit fly (*Drosophila melanogaster*), built from the FlyWire connectome. It lives in a small 2D world. Next to the living fly runs a **ghost**: a copy of the same brain that runs ahead and shows the fly's future.

A ghost that knows the brain *perfectly* is always right; that is what deterministic means, and the project says so openly: the perfect ghost is the **control**. The real question is the demon's: **how much must you know about a brain to foresee it, and where does that knowledge stop mattering?** So the viewer can give the ghost *imperfect* knowledge, and watch how long it stays right before it peels away, usually at a moment where the fly is deciding something.

Then **free will**: one extra spike, aimed where the brain is on an edge, and the future splits into a fan of timelines. Some collapse back together. Some never do. Many different brain futures turn out to share one behaviour.

That is the whole product in one screen:

1. **The live fly.** A real wiring diagram walking, turning, feeding and fleeing in a 2D arena (computed ahead of the screen, ADR-0030).
2. **The ghost.** The perfect ghost as the labelled control, and a **"how much does the ghost know?" slider** for the imperfect one.
3. **The fan.** On "free will", N branched futures drawn as diverging paths, with divergence measures.
4. **The brain.** Which neurons are firing, in the live fly and in each future.

Behind the screen, three measured results are the project's substance: the **predictability horizon** against measurement precision; the **brain's contribution** (real wiring against a shuffled "null brain"); and a **perturbation atlas** (how often, and where, one spike changes behaviour).

### 1.2 Why it matters (the North Star)

People have already made the fly connectome play Doom, Katamari, Clone Hero, poker and scroll videos. Those are demos of *control*. Tramlines is a demo of *meaning*. It makes visible, in a way anyone can feel in ten seconds, the oldest question the sci-fi canon keeps asking:

> If a mind is a machine, and the machine is deterministic, is its future already written? And how much would you need to know to read it?

The project succeeds when a stranger watches the clip for 30 seconds and *gets it*: they feel the chill of the ghost being right, then see it peel away the moment it knows one spike too little, and the strange relief when free will splits the future.

### 1.3 The Definition of Done for v1.0

Reframed by ADR-0035 (owner-adopted 2026-10-23). The original list is preserved at tag `v0.4.0`.

- [ ] Full FlyWire v783 brain (~138k neurons) drives a fly in a 2D world, with **no neuron both driven and read** (enforced by a test).
- [ ] The perfect ghost is **bit-exact** (the sacred tests) and shown openly as the control.
- [ ] **Result 1, predictability horizon:** how long an imperfect ghost stays right, against how precisely it knows the brain.
- [ ] **Result 2, the brain's contribution:** behaviour on the real connectome against a degree-preserving shuffled null brain.
- [ ] **Result 3, perturbation atlas:** the fraction of single spikes that change behaviour, where and when, and whether the tipping points survive changes to the decoder.
- [ ] Free will produces a fan of ≥ 8 aimed futures with divergence measures.
- [ ] A web viewer with the control ghost, the knowledge slider, the fan and the aesthetic in section 9.
- [ ] A long-form write-up (or preprint) with the data and scripts, after a literature check.
- [ ] The Book (scope under review: owner decision).
- [ ] Every decision recorded as an ADR.
- [ ] An honesty page (section 4) linked from the main screen.
- [ ] A 30–60 second launch clip.

---

## 2. Authority and the Deviation Protocol

This project has one author of intent: the owner. You are the builder. You are excellent, fast and opinionated, and you document every opinion. But you do not change direction.

### 2.1 Three kinds of decisions

| Kind | Who decides | What you do |
|---|---|---|
| **Locked** (section 3) | Already decided by the owner | Follow it exactly. Never reopen it. If you believe it is wrong, write an ADR with status `Challenge`, explain why, and keep following the locked decision until the owner answers. |
| **Delegated** | You | Make the call, write an ADR with status `Accepted (delegated)`, continue working. Examples: internal function names, file splits, test structure, plotting library details, CSS details within the design system. |
| **Reserved** | The owner only | Write an ADR with status `Proposed — awaiting owner`, list options with trade-offs and your recommendation, then **stop work on that path** and work on something unblocked. |

### 2.2 What is always Reserved

- Anything that changes the concept, the experience in section 1.1, or the phase order.
- Adding, removing or swapping a language, framework, runtime or major dependency.
- Changing the dataset or dataset version.
- Changing neuron model equations or the published parameters (section 7.2).
- Choices about which neurons count as "sensory inputs" or "motor outputs" (section 8) beyond what is written here.
- Anything that affects licensing, public release, branding, the project name, or what is claimed publicly about the science.
- Starting any "Future Season" (section 15).
- Deleting or rewriting a chapter of The Book that the owner has marked as reviewed.

### 2.3 When in doubt

If you cannot tell whether a choice is Delegated or Reserved, it is Reserved.

---

## 3. Locked decisions (already made by the owner)

Each of these has an ADR in `docs/decisions/` created during Phase 0. Write them from this table.

| # | Decision | Reason |
|---|---|---|
| L1 | The concept is the **Devs-style prediction machine** described in section 1, **reframed as an honest Laplace's demon** (ADR-0035, owner-adopted 2026-10-23). | Novel, buildable, concept-first. Game demos are saturated. The reframe makes the prediction an experiment instead of a tautology. |
| L2 | Dataset: **FlyWire v783** (public release) for the brain. | It is what Shiu et al. and Eon's fly-brain use. Proven model, available data. |
| L3 | Neuron model: **leaky integrate-and-fire** per Shiu et al. 2024 (*Nature*). | Published, validated against real fly behavior, simple enough to teach. |
| L4 | Core language: **Python 3.12**. Simulation engine: **PyTorch**. | Reuses the existing model and data tooling. Rich ecosystem. |
| L5 | Phase 1 viewer: **TypeScript** in the browser. Transport: **FastAPI + WebSockets**. | Shareable, visual, standard. |
| L6 | World: **2D top-down arena** first. No MuJoCo / NeuroMechFly / FlyGym in v1. | The concept needs paths, not leg physics. 3D body is a Future Season. |
| L7 | Determinism first: **CPU, float64, deterministic algorithms, seeded per-timeline RNG**, until the bit-exact prediction test passes. GPU only after that. | The illusion dies if the ghost is wrong even once. |
| L8 | Forking shares the **immutable weight matrix**; a fork copies only state (voltages, conductances, refractory timers, delay buffer, RNG state, world state). | Makes many futures cheap (a few MB each). |
| L9 | Phase 2 target: run the whole thing **in the visitor's browser** (WebGPU or JS), no server needed. | A link beats a video. |
| L10 | **Honesty is a feature.** The project states clearly what the model is and is not (section 4). | Credibility with scientists. Integrity. |
| L11 | The repository ships **The Book**: a from-zero learning path that builds this exact project (section 12). | The owner's requirement: someone who has never written Hello World can follow it. |
| L12 | The development environment uses **uv** for Python, **Vite** for the frontend, **MkDocs Material** for docs, **pytest** for tests, **ruff** for lint/format, **mypy** for types, **git** for history. | Modern, fast, simple to install. |

---

## 4. Honesty principles (the science contract)

Put this on a page called `docs/honesty.md` and link it from the viewer. Use your own words, accurate to this list:

1. **What it is.** A simulation driven by the measured wiring of a real adult fly brain. Every neuron and every connection count comes from electron-microscopy reconstruction by the FlyWire consortium.
2. **What it is not.** It is not the fly. The neuron model is simplified: every neuron uses the same parameters, there are no neuromodulators, no gap junctions, no learning, no glia and no hormones. Connection strength is approximated from synapse counts. Neurotransmitter identity is predicted from images.
3. **The body is ours, not the fly's.** FlyWire is the brain only. The mapping from brain outputs to movement in the 2D world is a design decision we made, documented in ADRs. Much of the "behavior" depends on that mapping.
4. **Determinism is a property of the simulation**, not a claim about real flies or about free will. The project is a thought experiment you can touch, not evidence for any philosophical position.
5. **Credit.** The connectome is the work of hundreds of people. Cite them properly (section 16).

Never write marketing copy that says "we uploaded a fly", "this fly is conscious", or "we proved determinism". The owner may choose bolder framing. That is Reserved.

---

## 5. Decision records (ADRs): the decision log is part of the product

Every decision lives in `docs/decisions/NNNN-short-title.md`, numbered from 0001, never renumbered, never deleted. Superseded decisions stay with status `Superseded by NNNN`.

### 5.1 ADR template

```markdown
# NNNN — Title in plain words

- Status: Locked | Accepted (delegated) | Proposed — awaiting owner | Challenge | Superseded by NNNN
- Date: YYYY-MM-DD
- Phase: N
- Decider: Owner | Claude (delegated)

## Context
What problem, what forces, what constraints. Plain language first, then technical.

## Options considered
1. Option A — pros / cons
2. Option B — pros / cons
3. (at least two real options, always)

## Decision
What we chose, in one sentence, then details.

## Consequences
What this makes easy, what it makes hard, what we must watch for.

## For learners
2–5 sentences explaining this decision to a beginner reading The Book. Link the chapter where it matters.
```

### 5.2 Rules

- The `For learners` section is mandatory. Decisions are teaching material.
- Link every ADR from the relevant Book chapter, and every chapter from relevant ADRs.
- Keep `docs/decisions/index.md` updated as a table: number, title, status, phase.

---

## 6. The inspiration canon

These works are the emotional and design source of the project. They shape the experience, the language of the UI and the narrative of The Book. **Never** use footage, screenshots, music, logos, character names, quotes or other copyrighted material from them in the product, the docs or the launch materials. Evoke the ideas; build our own expression.

| Work | What it gives Tramlines |
|---|---|
| **Devs** (FX/Hulu, 2020) | The core. A machine that projects the future of a deterministic world. The "tram lines" metaphor: life runs on rails it cannot leave. The many-worlds counter-idea. The golden, sacred, silent aesthetic of the machine. **Primary design reference.** |
| **Black Mirror: Hotel Reverie** (S7E3) | A copied mind inside a constructed world that does not know it is constructed. Informs the honesty page and the Future Season "Reverie". |
| **Black Mirror: USS Callister** & **Into Infinity** (S4E1, S7E6) | Digital copies of minds, forks with their own fates. Informs the branching fan: every branch is a copy that becomes its own. |
| **Black Mirror: White Bear** (S2E2) | A being trapped in a loop it cannot see the shape of. Informs the "replay" mode: run the same timeline again and watch it repeat exactly. |
| **Black Mirror: Playtest** (S3E2) | Simulation layered inside simulation, the subject never sure where the edge is. Informs nested ghosts (a ghost that predicts its own ghost). |
| **Black Mirror: Black Museum** (S4E6) | Copied consciousness as exhibit, and the ethics of it. Informs the brain-region "museum" view and the honesty tone. |
| **Pantheon** (AMC/Netflix) | Uploaded Intelligence. The scan-to-mind pipeline taken seriously, the technical texture of uploads. Informs the "pipeline" chapters of The Book. |
| **Pluto** (Netflix, 2023) | Machines with inner lives, grief and choice. Informs the emotional register: respect for the simulated thing. |
| **Altered Carbon** | Minds as data, bodies as sleeves. Informs the architecture separation: the brain (stack) is independent of the body (sleeve), so a Future Season can resleeve it into a robot. |
| **Common Side Effects** (Adult Swim, 2025) | Biology as a frontier hiding in plain sight. Informs the curiosity tone of The Book. |
| **Cyberpunk: Edgerunners** | Ambition, the cost of chasing greatness, neon on dark. Informs the secondary accent palette and the drive behind the launch. |
| **Scavengers Reign** (2023) | Alien, interconnected biology that is beautiful and strange. Informs how we draw the neurons: organic, living, not clinical. |

Reference links the owner shared (for context and citation, not for copying):

- Google Research, male fly brain milestone: https://research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/
- NIH Research Matters, complete adult fly brain wiring map: https://www.nih.gov/news-events/nih-research-matters/complete-wiring-map-adult-fruit-fly-brain
- Virtual Fly Brain: https://www.virtualflybrain.org/ and the JRC2018Unisex template viewer: https://v2.virtualflybrain.org/org.geppetto.frontend/geppetto?id=VFB_00101567&i=VFB_00101567
- natverse MaleCNS: https://natverse.org/malecns/ and https://github.com/natverse/malecns
- Filmmaker Magazine on Devs: https://filmmakermagazine.com/109907-quantum-entanglement/
- Community scene: https://x.com/wormuth and https://x.com/wormuth/status/2096409780961059119
- a7t (AI behavior experiments, an example of publishing experiments transparently): https://a7t.org/

Technical lineage (study before building):

- Eon Systems fly-brain (multi-backend Shiu LIF): https://github.com/eonsystemspbc/fly-brain
- Shiu et al. reference model: search GitHub for `philshiu/Drosophila_brain_model`, verify it before use.
- dotFly (honest, engineering-first write-up): https://kokosa.dev/blog/2026/dotfly/
- awesome-fruit-fly: https://github.com/townie/awesome-fruit-fly
- awesome-fly: https://github.com/cobanov/awesome-fly
- FlyWire Codex (cell types, annotations): https://codex.flywire.ai/

---

## 7. The science core

### 7.1 The data

- Source: FlyWire v783 public release. Two files form the brain:
  - a **neuron list** (completeness file, one row per neuron, root ID per neuron);
  - a **connectivity table** (parquet: presynaptic ID, postsynaptic ID, synapse count, predicted neurotransmitter or sign, weight).
- Expected filenames (as in Eon's repo): `2025_Completeness_783.csv` and `2025_Connectivity_783.parquet`. **Verify the exact names, columns and download source in Phase 0** and record them in an ADR. Store a checksum (SHA-256) of each file in `data/MANIFEST.md`.
- Cell type annotations come from FlyWire Codex. Record the exact annotation release used.
- **Root IDs change between FlyWire versions.** Never mix IDs from different versions (for example, v630 IDs seen in other projects). Every ID in this repo is v783 and is looked up by cell type from annotations, never typed in by hand from a blog post.
- Data files are **not committed** to git. A script `scripts/fetch_data.py` downloads and verifies them.
- Licensing: FlyWire data is CC BY 4.0, so attribution is required (section 16). The Virtual Fly Brain JRC2018Unisex template is CC-BY-NC-SA 4.0. Do **not** bundle it; it is reference only.

### 7.2 The neuron model (Shiu et al. 2024)

Each neuron *i* has a membrane voltage `v_i` and a synaptic conductance-like input `g_i`.

```
dv_i/dt = ( g_i − (v_i − V_rest) ) / τ_m
dg_i/dt = − g_i / τ_syn

if v_i ≥ V_th:
    neuron i spikes
    v_i ← V_reset
    neuron i is refractory for t_ref (v held at V_reset)

when a spike from neuron j arrives at i (after delay t_delay):
    g_i ← g_i + w_syn × W_ij
```

`W_ij` is the signed synapse count from *j* to *i*: positive for excitatory (acetylcholine), negative for inhibitory (GABA, and glutamate as treated in Shiu et al.).

Reference parameter values (from Shiu et al. as commonly reproduced; **verify each against the reference code in Phase 1 before use, and record the verified table in an ADR**):

| Parameter | Value |
|---|---|
| V_rest | −52 mV |
| V_reset | −52 mV |
| V_th | −45 mV |
| τ_m | 20 ms |
| τ_syn | 5 ms |
| t_ref | 2.2 ms |
| t_delay | 1.8 ms |
| w_syn | 0.275 mV per synapse |
| dt | 0.1 ms |
| Poisson input scaling | as in reference code |

If the reference code disagrees with this table, **the reference code wins**. Write a `Challenge` ADR noting the difference.

Sensory stimulation: chosen neurons receive Poisson spike trains at a set rate (for example 150–200 Hz). Each input event raises the target's `g` like a synaptic spike, scaled as in the reference code.

### 7.3 Phase 1 scientific acceptance test

Reproduce the canonical result: activating **sugar gustatory receptor neurons** drives the **MN9 proboscis motor neuron** to fire (the feeding response). Take the sugar GRN set and MN9's v783 ID from the reference code or annotations, not from memory. Plot the firing rate of MN9 against stimulus rate. Commit the plot to `docs/assets/` and explain it in The Book. If it fails, nothing after it is trusted.

---

## 8. Senses in, movement out (the brain–world interface)

This is where honesty matters most (section 4.3). Every mapping is an ADR.

### 8.1 Proposed sensory ports (status: Proposed — awaiting owner in Phase 3)

| World event | Neurons stimulated (by cell type, v783 annotations) | Rationale |
|---|---|---|
| Fly stands on food | sugar GRNs | Validated pathway (7.3) |
| Fly stands on bitter patch | bitter GRNs | Aversive taste, suppresses feeding |
| Looming shadow (threat) | looming-sensitive visual projection neurons (e.g. LC4 / LPLC2 families) | Known escape pathway |
| Wind / touch at boundary | antennal mechanosensory (Johnston's organ) neurons | Simple, well annotated |

### 8.2 Proposed motor decoder (status: Proposed — awaiting owner in Phase 3)

Read firing rates of descending neurons over a sliding window (for example 50 ms) and convert them to movement:

| Movement | Read from | Literature anchor to check |
|---|---|---|
| Forward speed | P9 and BPN descending neurons | Bidaye et al. 2020 |
| Turning | left–right difference of DNa02 (and DNa01) | Rayshubskiy et al. 2020 |
| Backward walking | MDN ("moonwalker") | Bidaye et al. 2014 |
| Escape jump | Giant Fiber (GF) | classic escape circuit |
| Feeding (stop + extend) | MN9 | Shiu et al. 2024 |

The decoder is **pure and deterministic**: same rates in, same movement out. Its gains and thresholds are constants in one file, `tramlines/world/decoder.py`, each one explained in an ADR.

### 8.3 The closed loop

```
world state ──▶ sensory ports ──▶ Poisson inputs ──▶ BRAIN (LIF, dt=0.1 ms)
     ▲                                                     │
     │                                                     ▼
 world.step(motor) ◀── motor decoder ◀── descending neuron spikes
```

The brain runs at dt = 0.1 ms. The world and decoder update every **1 ms of simulated time** (10 brain steps), which is an ADR. All of it is part of the forkable state.

---

## 9. Design and aesthetic direction

### 9.1 Mood

Sacred, silent, golden, inevitable. A cathedral of computation. The viewer should feel they are looking into the machine from Devs without seeing anything copied from it.

### 9.2 Palette (tokens, defined once in `web/src/styles/tokens.css`)

- Void: near-black background (`#07070a`).
- Gold: the live fly and the "true" timeline (warm amber gold, echoing the gold of the VFB brain render the owner shared).
- Ghost: the same gold at low opacity with a soft blur. The future is fainter than the present.
- Branch hues: a restrained spectrum for the fan, desaturated, never rainbow-loud.
- Accent (sparingly): a single Edgerunners-style electric cyan or magenta for the free will button and divergence meter.

### 9.3 Screen composition (Phase 4 target)

```
┌──────────────────────────────────────────────────────────────┐
│ TRAMLINES                      t = 00:12.340   ● LIVE        │
├───────────────────────────────────────┬──────────────────────┤
│                                       │  BRAIN ACTIVITY      │
│        ARENA (top-down 2D)            │  (neuron cloud or    │
│   gold fly ──── · · · ghost path      │   raster, firing     │
│        food ●   bitter ●              │   glows gold)        │
│                                       ├──────────────────────┤
│                                       │  PREDICTION          │
│                                       │  horizon: 3.0 s      │
│                                       │  match: 100.000%     │
├───────────────────────────────────────┴──────────────────────┤
│  [ FREE WILL ]   branches: 8   divergence ▁▂▃▅▇  [ REPLAY ]  │
└──────────────────────────────────────────────────────────────┘
```

### 9.4 Typography and motion

- One serif for display (for the sacred feel) and one monospace for numbers. Choose them in an ADR from Google Fonts.
- Motion is slow and smooth. Nothing bounces. The fan of futures unfolds like light through a prism.
- Respect `prefers-reduced-motion`.

---

## 10. The roadmap (phases, in order, with gates)

Never start phase N+1 until phase N's gate passes and the owner has said "go" in a session. Each phase ends with: tests green, ADRs written, Book chapters written and tested, journal entry.

### Phase 0 — Foundations
- Create repo structure (section 11), `pyproject.toml` with uv, ruff, mypy, pytest, MkDocs site skeleton, Vite + TypeScript skeleton.
- Write ADRs 0001–0012 from the locked table (section 3).
- `scripts/fetch_data.py` downloads FlyWire v783 files and verifies checksums.
- Study the Eon and Shiu reference code; write `docs/science/reference-model-notes.md` describing exactly how they load data, build weights and run.
- **Gate:** `uv run pytest` passes (smoke tests), `uv run mkdocs serve` shows the site, data loads and prints `neurons: ~138k, connections: N` with numbers recorded.

### Phase 1 — Hello, brain
- Implement `tramlines/brain/` LIF engine in PyTorch: CSR/sparse weights, ring-buffer synaptic delay, Poisson inputs, spike recording.
- Reproduce the sugar → MN9 result (section 7.3). Optionally cross-check one run against Eon's backend for matching spike counts.
- **Gate:** MN9 response plot matches the published qualitative result. Engine runs 1 s of simulated time; record wall-clock time on the owner's machine in the journal.

### Phase 2 — The fork (determinism)
- Implement `BrainState` (all mutable state, including the RNG state and delay buffer) and `Brain.fork() -> Brain` sharing weights.
- Determinism mode: CPU, float64, `torch.use_deterministic_algorithms(True)`, fixed thread count, per-timeline `torch.Generator`.
- **Bit-exact tests:** (a) run A for T; fork B at time t; run both to T; spike rasters and state must be identical. (b) Run the same seed twice in separate processes: identical. (c) Save/load state to disk: identical continuation.
- **Gate:** all three tests pass 100/100 times, across 10 seeds.

### Phase 3 — A body and a world
- `tramlines/world/`: 2D arena, fly kinematics, food/bitter patches, looming events, walls.
- Sensory ports and motor decoder (section 8). **Requires owner approval of the 8.1 and 8.2 ADRs before implementation.**
- World state is part of the forkable state. Determinism tests now include world state.
- **Gate:** headless run produces a fly trajectory PNG showing purposeful behavior (approaches food, stops, extends; flees a looming shadow). Determinism tests still 100% pass.

### Phase 4 — The ghost and the viewer
- `tramlines/server/`: FastAPI app streaming over WebSocket: fly pose, recent spikes (compressed), ghost path, prediction metadata.
- Projection, not live (ADR-0030, owner-approved 2026-10-23): a compute worker keeps the timeline several seconds ahead of the screen; the screen plays it at real speed (the live fly), and the ghost is the same timeline drawn further ahead. In a deterministic simulation this is identical to simulating live. Show the compute lead on screen; if it runs short, pause honestly rather than fake.
- `web/`: Vite + TS viewer. Canvas 2D first for the arena; neuron view as a 2D projection of soma positions (from annotation coordinates) or a raster. Three.js only if an ADR justifies it.
- Live "match %" meter comparing the live path to the ghost's prediction for the same time window. It must read 100.000% in determinism mode.
- **Gate:** owner watches the ghost lead and the fly follow, perfectly, for 60 s.

### Phase 5 — The demon's limits, and free will (reframed by ADR-0035)
- **Disjoint inputs and readouts:** no neuron both driven and read; a test enforces it (owner decision 17).
- **Result 1, predictability horizon:** a state-perturbation function (voltage error 10⁻¹²…10⁻³ mV, a dropped in-flight spike, float32 rounding, partial observation) and a sweep measuring how long the imperfect ghost stays right.
- **Result 2, null brain:** a degree-preserving shuffle of the connectome under the same senses, decoder and arena; report the behavioural difference.
- **Result 3, perturbation atlas:** single-spike sweeps across neurons and moments (screened cheaply at spike level, behaviour only for cascades), plus a decoder robustness check (100 ms window, thresholds ±20%).
- **Viewer:** the knowledge slider, and the perfect ghost labelled as the control.
- Button: fork N branches (default 8); each gets one extra spike, a different neuron per branch, logged and shown on screen; run all ahead H seconds. **Aimed (ADR-0031, owner-approved 2026-10-23):** the spike goes into a neuron currently receiving input, and the button is offered at decision moments; a uniformly random neuron almost never changes the future in this model (ADR-0029).
- Divergence metrics: (a) arena path distance over time; (b) spike-raster Hamming distance over time; (c) "time to divergence" (first step where behavior differs by > ε).
- Visualize the fan. Highlight branches that re-converge versus those that never do.
- "Replay" mode (White Bear): rerun from a saved state and show the identical loop.
- Batched branches in PyTorch (state as [neurons × B] tensors) are a delegated optimization **only if** determinism tests still pass.
- **Gate:** clip-worthy moment: the fan unfolds smoothly; the divergence meter is meaningful; a stranger understands it in 30 s (owner tests with a real person).

### Phase 6 — Polish and launch prep
- Aesthetic pass (section 9), honesty page, about page with credits, performance budget, mobile layout.
- Record the launch clip (screen capture). Script it in `docs/launch/clip-script.md`. Owner approves.
- Long-form write-up of the three results, with data and scripts, after a literature check (London et al. 2010; van Vreeswijk & Sompolinsky 1996).
- **Gate:** owner sign-off.

### Phase 7 — Into the browser (L9)
- **Open owner decision (ADR-0035):** ship precomputed runs plus a browser player instead of a live in-browser engine. Recommended; changes how L9 is met.
- Port the engine to the browser: WebGPU compute (preferred) or JS/WASM fallback. Data packed into a compact binary format (CSR, int32 indices, float32 weights), fetched once and cached.
- Note: float32 on GPU changes numerics. Determinism *within* the browser engine is still required (fixed reduction order); bit-exactness to the Python engine is not. Document this in an ADR.
- **Gate:** a public static link runs the full experience on a mid-range laptop.

### Phase 8 — Release
- Owner decides license, name, launch channels. All Reserved.

---

## 11. Repository layout

```
tramlines/
├── CLAUDE.md                    # this file
├── ROADMAP.md                   # phase checklist, current status at top
├── README.md                    # what it is, the clip, how to run, credits
├── pyproject.toml               # uv-managed
├── data/
│   ├── MANIFEST.md              # file names, sources, versions, SHA-256
│   └── (downloaded files, git-ignored)
├── scripts/
│   ├── fetch_data.py
│   └── run_headless.py          # experiments without the viewer
├── tramlines/
│   ├── brain/
│   │   ├── data.py              # load neurons + connectivity → tensors
│   │   ├── params.py            # verified LIF parameters (one place only)
│   │   ├── engine.py            # Brain: step(), run(), fork()
│   │   ├── state.py             # BrainState dataclass, save/load
│   │   ├── inputs.py            # Poisson stimulation
│   │   └── neurons.py           # lookup by cell type → v783 IDs → indices
│   ├── world/
│   │   ├── arena.py
│   │   ├── fly.py
│   │   ├── senses.py            # world → sensory ports
│   │   └── decoder.py           # descending spikes → movement
│   ├── timeline/
│   │   ├── timeline.py          # brain + world + clock, forkable as one
│   │   ├── ghost.py             # run-ahead prediction
│   │   ├── branches.py          # free will fan
│   │   └── divergence.py
│   └── server/
│       ├── app.py               # FastAPI + WebSocket
│       └── protocol.py          # message schemas (pydantic)
├── tests/
│   ├── test_determinism.py      # the sacred tests
│   ├── test_sugar_mn9.py
│   └── ...
├── web/                         # Vite + TypeScript viewer
│   ├── src/
│   │   ├── main.ts
│   │   ├── arena.ts
│   │   ├── brainView.ts
│   │   ├── socket.ts
│   │   └── styles/tokens.css
│   └── index.html
├── book/                        # The Book's runnable code, chapter by chapter
│   ├── ch01/ ... ch30/
└── docs/                        # MkDocs site
    ├── index.md
    ├── honesty.md
    ├── book/                    # The Book chapters (markdown)
    ├── decisions/               # ADRs + index.md
    ├── architecture/            # diagrams, data flow, protocol
    ├── science/                 # model notes, verified parameters, citations
    ├── journal/                 # one entry per session
    └── launch/
```

---

## 12. The Book: "Tramlines: Building a Machine That Sees the Future"

### 12.1 Its promise

A reader who has never written a line of code starts at Chapter 0 and ends having built every part of Tramlines themselves, understanding why each part exists. The project is not simplified. The *path* is made gentle. Every chapter ends with something real running on the reader's machine.

The Book should feel like the book that changes someone's direction: the moment where neurons, code, determinism and free will suddenly connect. Write for that moment.

### 12.2 Voice

- Second person, warm, direct, never condescending. Assume the reader is smart and new.
- Short paragraphs. One idea at a time. Define every term the first time, with a link to the glossary.
- Use the inspiration canon as narrative (describe the *ideas* in our own words; never quote the shows).
- Concrete before abstract. Run it first, explain it second, generalize third.
- Honest about difficulty: "this part is hard; here is why; here is how to get through it."
- No filler, no hype, no "simply" or "just".

### 12.3 Chapter template (every chapter)

```markdown
# Chapter N — Title

> One-line hook: a question or a scene.

## Where we are
Two sentences: what you can do now, what this chapter adds.

## The idea
The concept in plain language, with one analogy.

## Build it
Numbered steps. Every command and every line of code, typed in full.
Code lives in book/chNN/ and is tested.

## Run it
Exact command. Exact expected output (or a picture of it).

## The click
What just happened, and how it connects to the bigger machine.
This is the most important section. Make it land.

## Break it
2–4 experiments: change one thing, predict, run, see.

## When it goes wrong
The 3 most likely errors and how to fix them.

## Check yourself
3–5 questions, answers at the bottom of the page in a collapsed block.

## Decisions in this chapter
Links to the ADRs that shaped this code.

## Next
One sentence pulling the reader forward.
```

### 12.4 The table of contents (target; you may refine chapter splits as a delegated decision, but not remove parts)

**Part 0 — The Door**
- 0. Why a fly, why now: the connectome story, the shows, and what you will build.
- 1. Your computer, opened up: files, folders, the terminal, without fear.

**Part I — First Words**
- 2. Installing Python with uv. *Hello, world.* Your first program.
- 3. Values and variables: the computer's memory as labeled boxes.
- 4. Decisions and loops: if, for, while; teaching the machine to repeat.
- 5. Functions: naming an idea so you can use it again.
- 6. Lists, dictionaries and files: reading a CSV of real neurons.
- 7. Git: saving your progress through time (your first "timelines").

**Part II — One Neuron**
- 8. What a neuron is: biology for engineers, in one chapter.
- 9. Simulating time: dt, Euler steps, why a computer's time is a staircase.
- 10. One leaky integrate-and-fire neuron in plain Python; plotting its voltage.
- 11. Two neurons talking: synapses, weights, delay.
- 12. Randomness and seeds. **The first click**: a "random" program that does the same thing every time.

**Part III — The Whole Brain**
- 13. How the connectome was made: electron microscopes, AI segmentation, thousands of proofreaders.
- 14. NumPy: from one neuron to a thousand at once (vectors).
- 15. Sparse matrices: storing 15 million connections without running out of memory.
- 16. PyTorch: the engine that runs the brain.
- 17. Loading FlyWire v783: the real data, the real numbers.
- 18. **The brain wakes up**: sugar on the tongue, MN9 fires. Reproducing a *Nature* result on your laptop.

**Part IV — The Machine (Devs)**
- 19. State: everything a brain *is* at one instant.
- 20. Forking: copying a mind without copying its wiring.
- 21. The sacred tests: proving two timelines are identical, bit for bit.
- 22. The ghost: running a copy into the future.
- 23. **Free will**: one spike, and the future splits.
- 24. Measuring divergence: how different are two futures?

**Part V — A Body and a World**
- 25. A 2D world and the game loop.
- 26. Senses in, movement out, and why this is the least certain part of the science (honesty chapter).

**Part VI — Showing It**
- 27. The web in one chapter: HTML, CSS, TypeScript.
- 28. WebSockets: a live wire from the brain to the screen.
- 29. Drawing the machine: canvas, the gold, the ghost, the fan.

**Part VII — Setting It Free**
- 30. Into the browser: WebGPU and running a brain on a visitor's machine.
- 31. Shipping: tests, performance, telling the story, the launch clip.
- 32. What this is not, and what comes next: mouse brains, Pantheon, and the questions you now own.

**Appendices**
- A. Glossary.
- B. Troubleshooting index.
- C. The math, gently: differential equations without fear.
- D. Reading a scientific paper.
- E. Citations and credits.

### 12.5 Book rules

- Every code block in The Book corresponds to a file in `book/chNN/` and is run by CI (`tests/test_book.py` executes each chapter's scripts and checks expected output). A chapter whose code fails is a failing build.
- Write chapters **alongside** the phase that builds that code, not at the end.
- Early chapters (Parts 0–II) may be written in Phase 0–1 because they need no project code.
- The owner reviews chapters and marks them `<!-- reviewed: owner YYYY-MM-DD -->`. Do not rewrite reviewed chapters without permission (2.2).
- Diagrams: Mermaid in markdown, or SVG in `docs/assets/`. Every diagram has alt text.

---

## 13. Engineering standards

### 13.1 Code

- Python: type hints everywhere, `ruff format`, `ruff check`, `mypy --strict` on `tramlines/`.
- Functions are small and named for what they mean ("inject_free_will_spike", not "do_branch").
- One source of truth for constants: `params.py` (neuron model), `decoder.py` (motor gains), `config.py` (horizons, rates, branch counts).
- Docstrings explain *why*, not only *what*. Link ADRs by number in comments where a decision shaped the code.
- TypeScript: `strict: true`, no `any` without a comment.

### 13.2 Tests

- `tests/test_determinism.py` is sacred. It runs on every change. It is never weakened, skipped or marked flaky. If it fails, everything stops until it passes.
- Scientific regression: sugar → MN9 test with tolerance bands, recorded in an ADR.
- Book tests (12.5).
- Golden files: small saved spike rasters and trajectories for fixed seeds, compared exactly.

### 13.3 Performance budget (measure, don't guess)

- Record on the owner's machine: wall-clock seconds per simulated second, RAM peak, ghost compute time for H = 3 s.
- Under projection (ADR-0030) the engine must compute faster than the screen plays *on average*, using at most 3 parallel brain processes on the owner's machine (ADR-0029). Faster engines (batching, Numba/C++ kernel) shorten preparation and branch waits; changing language is Reserved.
- Expected memory: weights ~100–200 MB shared; ~2–5 MB per timeline state.

### 13.4 Session ritual

**Start:** read this file, the latest journal entry, `ROADMAP.md`, and open ADRs awaiting the owner.
**During:** small commits with clear messages (`brain: add ring-buffer synaptic delay (ADR-0017)`).
**End:** write `docs/journal/YYYY-MM-DD-session-N.md`:

```markdown
# Session N — YYYY-MM-DD
## Done
## Decisions made (ADR links)
## Waiting on owner
## Measurements (perf, test results)
## Next session starts with
```

Update the status block at the top of `ROADMAP.md`.

---

## 14. Glossary (seed; expand in docs/book/glossary.md)

- **Connectome**: the complete wiring diagram of a nervous system: every neuron and which neurons connect to which.
- **FlyWire**: the consortium and dataset that reconstructed the adult female fruit fly brain from electron microscopy.
- **MaleCNS**: the male fruit fly central nervous system connectome (brain plus nerve cord), released 2026.
- **Root ID**: FlyWire's unique number for one neuron in one data version.
- **LIF (leaky integrate-and-fire)**: a simple neuron model. Voltage leaks toward rest, rises with input, and the neuron "fires" when it crosses a threshold.
- **Spike**: a neuron firing; the brain's unit of signal.
- **Synapse**: a connection point where one neuron signals another.
- **Descending neuron**: a neuron sending commands from brain to body.
- **GRN**: gustatory receptor neuron; a taste sensor.
- **MN9**: a motor neuron controlling proboscis extension (the fly's "tongue").
- **Poisson input**: random spikes at an average rate, used to simulate a sensory stimulus.
- **Determinism**: same starting state + same inputs → same result, always.
- **Fork**: an independent copy of a timeline's state, continuing on its own.
- **Ghost**: a fork run ahead in time to predict the live fly's future.
- **Branch**: a fork that received one extra "free will" spike.
- **Divergence**: how far two timelines have moved apart.
- **ADR**: Architecture Decision Record; a short document explaining one decision.

---

## 15. Future Seasons (LOCKED OUT until the owner starts one)

Record ideas here; do not build them.

- **Season 2: Reverie.** Female (FlyWire) and male (MaleCNS) brains in one world; courtship circuits; two copied minds meeting.
- **Season 3: The Crew.** Many clones of one brain with tiny differences: do identical minds become individuals?
- **Season 4: The Endless Day.** A 24/7 public stream of one fly in a never-ending world; viewers drop stimuli.
- **Season 5: Resleeve.** The brain drives a physical robot (camera in, motors out). The stack leaves the sleeve.
- **Season 6: The Museum.** An explorable exhibition of the brain's circuits, region by region.
- **3D body.** NeuroMechFly v2 / FlyGym in MuJoCo.

---

## 16. Credits and citations (must appear in README and docs/science/citations.md)

Verify each citation's exact authors, title, venue and year before publishing:

- FlyWire consortium: Dorkenwald et al. 2024, *Nature* (whole-brain connectome) and Schlegel et al. 2024, *Nature* (cell type annotations).
- Shiu et al. 2024, *Nature*: whole-brain LIF model of the adult *Drosophila* brain.
- MaleCNS (Janelia/Google and collaborators), 2026 release and *Cell* paper.
- Eon Systems, fly-brain repository.
- Virtual Fly Brain and the JRC2018 templates (Bogovic et al.).
- natverse.
- Movement literature used in the decoder (Bidaye et al.; Rayshubskiy et al.; giant fiber escape literature).

---

## 17. Open questions for the owner (keep this list current)

1. Project name: "Tramlines" is a working title. Keep or change?
2. Code license (MIT / Apache-2.0 / GPL-3.0)?
3. Approve the sensory ports (8.1) and motor decoder (8.2) when Phase 3 arrives.
4. Default prediction horizon (3 s) and branch count (8)?
5. Launch channels and timing.
6. Owner's machine specs (CPU, RAM, GPU, OS) for the performance budget.

---

*Last edited by: Claude, at the owner's request. Changes to this file are Reserved: propose them as an ADR.*