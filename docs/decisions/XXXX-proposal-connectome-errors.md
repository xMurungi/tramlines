# XXXX — Proposal: how accurate must a connectome be? (realistic connectome errors)

- Status: **Proposed — awaiting owner** (owner decision 22)
- Date: 2026-10-24
- Phase: 5
- Decider: Owner
- Number: assigned by the main session when merged (written as XXXX here)

## Context
Result 2 ([ADR-0039](0039-result-2-null-brain.md)) asked what the real wiring contributes, by scrambling it at random. The fly survived a quarter of its connections rewired, and the first thing to break was its judgement: refusing bitter-laced food broke from 5%. But nobody's connectome is wrong *at random*. Real reconstructions are wrong in specific, measurable ways: synapses missed, false synapses added, transmitters (and so excitation or inhibition) predicted wrongly for whole neurons, and pieces of neurons cut off or wrongly attached.

**The question, in the demon's terms:** the demon's map of the wiring is a reconstruction, with the errors reconstructions really have. At the error rates published for FlyWire, does the model still produce the same fly? Which kind of error matters most, how much error can it take, and which behaviour breaks first?

**Why it matters beyond this project.** Every model built from a connectome, Shiu et al. 2024 included, assumes the reconstruction is good enough. This would measure how good is good enough, for one closed-loop whole-brain model, with each error type at its published rate. A connectome-modelling lab would read that.

**What the literature gives** (full table, sources and confidence: [`docs/science/connectome-error-rates.md`](../science/connectome-error-rates.md)):

| Error | Best published number | Measured or bound? |
|---|---|---|
| Missed synapses | FlyWire: "the dominant type of error", no rate published. Hemibrain (closest relative): synapse recall about 0.80. Detector on FAFB: F 0.59–0.75. Plus: only 44.7% of postsynapses attached to a proofread neuron. | No FlyWire rate; ~20% from the hemibrain |
| False synapses | FlyWire: "exist", no rate. Hemibrain: precision about 0.80, so about 0.25 false per true synapse. | No FlyWire rate; likely an upper estimate, since FlyWire says misses dominate |
| Wrong sign | 94% of neurons' transmitters right (87% of synapses); the commonest confusion (glutamate ↔ GABA) keeps the sign. Our data: the file's sign and the annotations' transmitter disagree for 4.4% of neurons. | Bound: ≤ 6% of neurons |
| Merge / split | 99.2% F1 by volume on 826 re-proofread neurons; separate rates not published. | No rate; bound only |
| Re-measurement | Only 53–59% of all connections are found in both of two reconstructions, but > 90% of those with > 10 synapses. | Upper bound (mixes errors with biology) |

**A framing that keeps this honest.** The model's synapse strength was calibrated by Shiu et al. on this incomplete table (ADR-0016). So the study cannot ask how far the model is from the true brain. It can ask: **would a second, equally good reconstruction of the same brain give the same fly?** The error rates say how different that second reconstruction would plausibly be.

## Instruments (built with this proposal; no study run)
`tramlines/brain/errors.py`, tested on the 400-neuron network in `tests/test_errors.py` (31 tests). Each is seeded, deterministic, returns a new connectome with the same neurons, keeps no self-connections, no repeated pairs and one sign per neuron, and is bit-identical to the real wiring at rate 0. Nothing existing was changed.

| Instrument | What it does | Choice made, and why |
|---|---|---|
| `drop_synapses(c, fraction, seed)` | Each synapse lost independently: a k-synapse connection keeps Binomial(k, 1 − fraction). | Per synapse, not per connection: weights shrink by count, and weak connections vanish first. Independence is FlyWire's own assumption for its 5-synapse threshold. |
| `add_synapses(c, rate, seed, onto=…)` | Adds round(rate × total synapses) false synapses, each with its sender's sign. | `"anywhere"` (default): sender drawn in proportion to its output synapses, receiver to its input synapses: synapse-dense neurons have more neurites side by side, the only proxy without geometry. Strengthens existing pairs or creates new one-synapse connections. `"existing"`: only onto existing connections, in proportion to their count (close to a scale-up with noise). The two bracket the effect. |
| `flip_signs(c, fraction, seed, among=…)` | Flips all outputs of exactly round(fraction × candidates) whole neurons. | Whole neurons, because transmitters are predicted per neuron. `among` restricts to one transmitter's neurons (from `top_nt`). Exact count rather than a coin per neuron, so every draw has the stated rate. |
| `with_signs(c, sign)` | Sets each neuron's sign from an array (0 keeps it). | For the second, published sign assignment: the annotations' `top_nt`, which disagrees with the file for 4.4% of neurons. Not random. |
| `split_neurons(c, fraction, share, seed)` | Chosen neurons lose each of their connections whole, with probability `share`. | A cut-off twig takes its synapses together: the correlated extreme, where `drop_synapses` is the independent one. Which connections share a twig is unknowable without synapse positions, so it is random. |
| `merge_neurons(c, fraction, share, seed)` | A donor's connections move to a host with probability `share`; outputs take the host's sign. | The donor is one of the host's partners (connected neurons touch, and merges join touching neurites). Neuron count unchanged; new self-connections dropped; repeated pairs summed. |
| `scaled(c, factor)` | Every weight × factor. | The control: dropping 20% of synapses also lowers the average drive by 20%; `scaled(c, 0.8)` separates the pattern of loss from the lower average. |

**Merge and split are feasible but weakly anchored:** no published rate, no synapse positions to make them spatially real. The proposal keeps them exploratory.

## Options considered
1. **Do it as a pre-registered study: a pilot, then a full sweep** (recommended). Design below. About 5–8 hours of computing in total.
   - Pros: answers a question modellers have and nobody (as far as I know; a literature check comes first) has answered for a closed-loop whole-brain model; reuses Result 2's probes and decoder-free test; the instruments are built and tested; turns the bitter-veto finding into a claim about realistic errors.
   - Cons: a fifth result to write up and show; the "measured" rates are partly from a relative dataset (hemibrain) and partly bounds; results depend on our senses and decoder (Result 2's yardstick caveat applies).
2. **Pilot only, reported as an exploratory section of Result 2.** One seed, one draw per condition, about 15 minutes.
   - Pros: almost free; enough to say whether realistic errors look harmless or not.
   - Cons: one seed and one draw, the weakness Result 1's first pass had (it was corrected by the second pass). Not a claim anyone should cite.
3. **Do not do it.** Keep v1.0 to four results.
   - Pros: focus on the viewer and the write-up.
   - Cons: Result 2's most useful finding (judgement breaks first) stays a statement about random damage, which no real connectome has.

(Considered and set aside: comparing the model on FlyWire's left and right hemispheres, or on FlyWire vs the hemibrain, as a "real" re-measurement. The model uses the whole brain at once, and the hemibrain is half a brain of another fly; it cannot be swapped in.)

## Design, if adopted (to be fixed in a pre-registered plan before the study runs)

**Brains and seeds.** Every condition: 3 error draws × 3 run seeds (0, 1, 2), the lesson of Result 1's second pass. The real brain: 3 seeds (rerun, since the code has changed since Result 2).

**Error types and rates.** Rates anchored on the literature, at the measured scale and at multiples. Where ×5 is impossible (losing more than all synapses), the multiples stop earlier.

| Condition | Rates | Anchor |
|---|---|---|
| Missed synapses (`drop_synapses`) | 0.1, **0.2**, 0.4 (×2), 0.6 (×3) | 1 − recall ≈ 0.2 (hemibrain); 0.6 is about the unattached share of postsynapses |
| False synapses (`add_synapses`, anywhere) | 0.05, 0.1, **0.25**, 0.5 (×2), 1.25 (×5) | (1 − precision)/precision ≈ 0.25 (hemibrain) |
| Wrong sign, any neuron (`flip_signs`) | 0.01, 0.02, **0.05**, 0.1 (×2), 0.25 (×5) | ≤ 6% (Eckstein et al.); 4.4% disagreement in our data |
| Wrong sign, one transmitter | 0.05 among acetylcholine, among GABA, among glutamate neurons | Which transmitter's errors matter most |
| The second published sign (`with_signs`, from `top_nt`) | one assignment (no draws), 3 seeds | A real alternative, not a random one |
| **Re-measurement** (all three together) | measured (0.2 / 0.25 / 0.05) and ×2 (0.4 / 0.5 / 0.1) | The headline: "a second reconstruction" |
| Controls (`scaled`) | 0.8, 0.6, 1.25, 1.5 (3 seeds; no draws) | Same average drive as missed 0.2, 0.4 and false 0.25, 0.5 |
| *Exploratory:* false synapses on existing pairs only | 0.25, 1.25 | Brackets "anywhere" |
| *Exploratory:* split | 5%, 20% of neurons, share 0.5 | No published rate |
| *Exploratory:* merge | 1%, 5% of neurons, share 0.5 | No published rate |

**Measurements, per brain (Result 2's, unchanged).** An arena run, and the clamped probes: 1 s each on walking ground, food, bitter, food laced with bitter, and under the shadow, with the same senses and decoder. Outcomes: walks, feeds on food, refuses laced food, escapes, stays quiet (active neurons as in ADR-0039). Plus Result 2's **decoder-free check** (which situation can be read from neurons 2+ synapses from any input; how deep sense-specific activity travels) for missed, false and wrong-sign errors at the measured and ×2 rates, draw 0.

**Candidate hypotheses** (to be made precise, with thresholds, in the plan):
- **H1, realistic errors are survivable:** at the measured rates, walking, feeding and escape survive in most brains (e.g. ≥ 80% of runs).
- **H2, judgement breaks first:** for each error type, refusing laced food is the first behaviour to fail as the rate rises (Result 2's pattern).
- **H3, signs matter more than synapses:** per synapse affected, wrong signs break behaviour sooner than missed synapses.
- **H4, missed synapses act mostly as lower drive:** `drop_synapses(p)` behaves like `scaled(1 − p)`; if not, the pattern of loss (weak connections vanishing) matters in itself.
- **H5, false synapses open new paths:** "anywhere" at ≥ 0.5 tips brains into runaway activity more often than the scaled control.
- **Q (no direction predicted):** does the fly behave the same under the annotations' signs (`with_signs`)?

**Pilot first** (exploratory, as in ADR-0040): seed 0, draw 0; missed, false and wrong-sign at measured and ×2; the second sign; the real brain. 8 brains, about 15 minutes. Its seed and draw are then excluded from confirmatory claims, or the plan says how they are used.

## Estimated compute
From Result 2's timings on this machine (ADR-0039): about 1–1.3 minutes of wall time per brain on 2 workers for an arena run plus the five probes, more for runaway brains.

| Part | Brains | Estimate |
|---|---|---|
| Pilot | 8 | ~15 min |
| Confirmatory (14 swept levels × 9, real × 3, re-measurement 2 × 9, per transmitter 3 × 9, second sign × 3, controls 4 × 3) | ~189 | ~3–4.5 h on 2 workers |
| Exploratory (existing-only, split, merge: 6 levels × 9) | 54 | ~1–1.2 h |
| Decoder-free (3 types × 2 rates × 3 seeds) | 18 | ~30–45 min |
| **Total** | **~270** | **~5–6.5 h**, plus about 1 h if runaway conditions run on 1 worker |

**Memory.** Wrong-sign and false-synapse brains are the likeliest to run away (losing inhibition, or new random paths); Result 2's runaway brains used up to 6.4 GB and pushed swap to 4 GB on 2 workers. Those conditions should start on 1 worker (suggestion 9), which could add about an hour. Building one errored full connectome costs seconds and about 1 GB transient memory (estimated from array sizes; not measured on the full brain, because Result 3 was using the machine).

## Recommendation
**Option 1**, after Result 3 finishes: the pilot, then a pre-registered plan merged before the full study, as Result 4 was. It is the version of Result 2 that applies to real connectomes, the instruments already exist, and it costs a night of computing.

## Reserved, for the owner
- **Adding a fifth result** changes CLAUDE.md 1.3 (Definition of Done) and Phase 5: the owner's amendment, as for ADR-0040.
- **Public claims about FlyWire's accuracy.** The write-up would cite published rates and say plainly which are bounds or from the hemibrain; any wording that could read as criticism of the FlyWire reconstruction is the owner's call. The 4.4% sign disagreement is a fact about two files, with an unknown cause; it should not be presented as an error in FlyWire until the cause is known (asking the FlyWire team would be outward-facing, also the owner's call).
- **No new dependencies** are needed.

## If adopted
- The honesty page gains a line: the model was tested against realistic reconstruction errors, with the result, whatever it is.
- Literature check before any novelty claim (connectome-constrained model robustness; e.g. work on how sensitive connectome-based models are to synapse-count and sign errors).

## For learners
A map is never the territory. A connectome is a map of a brain made by microscopes and software, and both make mistakes: they miss some connections, invent a few, and sometimes mistake a "go" signal for a "stop" signal. Result 2 asked what happens if the map is scrambled at random. This asks a sharper question: if the map has exactly the kinds of mistakes real maps have, in the amounts they really have them, does the simulated fly still do the same things? If yes, models built from connectomes are on firmer ground. If not, we learn which mistakes matter most, and which behaviour is the first to go.
