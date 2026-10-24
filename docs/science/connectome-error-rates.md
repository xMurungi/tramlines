# How wrong is the connectome? Published error rates for FlyWire v783

- Written 2026-10-24 for owner decision 22 ("how accurate must a connectome be?") and its proposal ADR.
- **Rule:** every number below comes from a source I read, with the source named. Where FlyWire has not published a number, the page says so and gives the closest published relative, labelled as such. Numbers marked *our measurement* come from the v783 files this project uses (`data/MANIFEST.md`), not from the literature.
- **How sure:** *high* = read in the published paper's text; *medium* = read in a preprint, or the published version may differ in detail; *low* = inferred or read only through a summary.

## In one paragraph

FlyWire's own papers say **missed synapses are the main error, false ones exist too**, and they give no precision or recall for the final synapse table. The detector behind it scores F 0.59–0.75 on hand-checked fly brain regions (Buhmann et al. 2021); in the closest relative, the hemibrain, the final synapses have about **0.80 precision and 0.80 recall** (volume-weighted over 43 brain regions). On top of detection, **only 44.7% of postsynaptic sites are attached to a proofread neuron**, so more than half of all detected input synapses are missing from any neuron-to-neuron table. Transmitters are predicted correctly for **87% of synapses and 94% of neurons** (test set), but the commonest confusion (glutamate with GABA) does not change the sign this model uses. Proofreading is good where it was checked (**99.2% F1 by volume** on 826 neurons), but merge and split rates are not published separately. Two reconstructions of the same circuits (FlyWire left vs right, FlyWire vs hemibrain) find **only 53–59% of connections in both**, but **over 90% of connections with more than 10 synapses**.

## 1. Synapse detection: false and missed synapses

| Number | What exactly it measures | Source | How sure |
|---|---|---|---|
| ~244 million synapses predicted; ~130 million kept | Buhmann et al.'s predictions over the whole FAFB volume; kept after removing synapses with either end unassigned to a segment, or a Heinrich et al. cleft score ≤ 50 ("to improve precision"), and duplicates within 100 nm. | Dorkenwald et al. 2024, *Nature* 634, 124–138, Methods. [PMC11446842](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842/) | high |
| "false negative synapses are the dominant type of error but false positives also exist" | A qualitative statement; no counts or rates are given. | Dorkenwald et al. 2024 | high |
| No precision or recall for the final FlyWire synapse table | I found none in Dorkenwald et al. 2024 (read through PMC: the main text, Methods and Discussion, about 86% of the page; the last part, mostly references and figure legends, was not read) or Schlegel et al. 2024. **Not published, as far as I can tell.** | — | medium (absence is harder to prove than presence) |
| F-score 0.73, 0.68, 0.66, 0.59 (0.75, 0.69–0.70, 0.67, 0.60 with cleft filtering) | Synaptic *partner* detection (a synapse counts only if both partner neurons are right, within 400 nm), against hand-annotated ground truth in calyx, lateral horn, ellipsoid body and protocerebral bridge of FAFB; the best F-score along each region's precision–recall curve. Precision and recall are not given separately in the text. The two published values for the lateral horn (0.69, 0.70) disagree between text and figure caption. | Buhmann, J., Sheridan, A. et al. 2021, *Nat. Methods* 18, 771–774. [PMC7611460](https://pmc.ncbi.nlm.nih.gov/articles/PMC7611460/); preprint [bioRxiv 2019.12.12.874172](https://www.biorxiv.org/content/10.1101/2019.12.12.874172v2) | high |
| precision 0.72, recall 0.77 (F 0.74) | The same detector on the CREMI validation set (a different, smaller benchmark). | Buhmann et al. 2021 | high |
| 92–96% of connections correctly called as ≥ 5 synapses or < 5 | With the predictions combined with a segmentation (calyx, lateral horn): the detector's errors largely cancel at the level of strong vs weak connections. | Buhmann et al. 2021 | high |
| Pair-level errors in the calyx: 28 neuron pairs (1%) false positive, 74 pairs (3%) false negative | Connections in the PairCalyx analysis, at the connection-score threshold used there. | Buhmann et al. 2021 (preprint text) | medium |
| **Closest relative, hemibrain: synapse precision median 0.84 (range 0.58–0.95), recall median 0.80 (0.55–0.93); volume-weighted 0.80 and 0.80** | Final hemibrain synapse predictions (T-bar plus postsynaptic density), per brain region (43 regions), against proofread ground truth. T-bars alone: precision 0.91, recall 0.93 (volume-weighted). Human proofreaders reach about 0.9 on T-bars and 0.8 on postsynaptic densities. Different microscope (FIB-SEM), different detector, different fly. | Scheffer, L. K. et al. 2020, *eLife* 9:e57443, Fig. 5 and its source data ([T-bars](https://cdn.elifesciences.org/articles/57443/elife-57443-fig5-data1-v4.csv), [synapses](https://cdn.elifesciences.org/articles/57443/elife-57443-fig5-data2-v4.csv)); medians and weighting computed by me from those files | high for the data; the summary statistics are mine |

**What this means for the model.** The model uses every connection in the v783 table, including the 50% that are a single synapse (*our measurement*: 49.7% of 15,091,983 connections have one synapse, 82.1% have fewer than five, and those under five carry 37.3% of all synapses). FlyWire's own analyses use only connections of ≥ 5 synapses, "likely to be adequate for avoiding false positives … but not missing connections", and call the cut-off "reasonable but arbitrary". The weak connections are where false synapses matter most.

## 2. Completeness: synapses missing because their twig was never attached

| Number | What exactly it measures | Source | How sure |
|---|---|---|---|
| **93.7% of presynapses, 44.7% of postsynapses attached** (~122 and ~58.1 million) | Share of detected synapse sites lying on a proofread neuron. Postsynapses sit on fine twigs, which were proofread less. (The 2023 preprint gives 92.3% and 43.9%.) | Dorkenwald et al. 2024 | high |
| Going from 44.7% to 50% "would require further proofreading of more than 700,000 fragments" | Cost of completion. | Dorkenwald et al. 2024 | high |
| 54,492,922 synapses in the table the model uses | *Our measurement* (`data/MANIFEST.md`): about 42% of the ~130 million kept synapses, consistent with both ends having to be attached. | this repository | high |
| Mushroom body postsynaptic completion: 46% (FlyWire right) to 77% (hemibrain) | Completion varies by region and dataset. | Schlegel et al. preprint ([bioRxiv 2023.06.27.546055](https://www.biorxiv.org/content/10.1101/2023.06.27.546055v2)) | medium |
| A 30-synapse hemibrain connection has on average 26 synapses in FlyWire; 25% of them have fewer than 10 | Matched connections between two reconstructions of two flies: detection and completion differences together, plus real biological differences. | Schlegel et al. preprint | medium |

**What this means for the model.** Missing input synapses are not a small correction: by attachment alone, more than half of all detected postsynaptic sites are absent from the table. The model's synapse weight (w_syn = 0.275 mV, ADR-0016) was set by Shiu et al. on this incomplete table, so the model is calibrated to it. The question a study can ask is therefore not "how far is the model from the true brain" but **"would a second, equally good reconstruction give the same fly?"**

## 3. Neurotransmitter prediction: the sign of every neuron

| Number | What exactly it measures | Source | How sure |
|---|---|---|---|
| **87% per synapse; 94% per neuron** (majority vote) | Six-way classification (acetylcholine, glutamate, GABA, serotonin, dopamine, octopamine) on a held-out test set split by whole neurons (185 neurons, 40,104 presynapses, FAFB-CATMAID). Per-neuron accuracy counts only neurons with > 30 test presynapses. HemiBrain: 78% and 91%. | Eckstein, N. et al. 2024, *Cell* 187(10), doi:10.1016/j.cell.2024.03.016. [PMC11106717](https://pmc.ncbi.nlm.nih.gov/articles/PMC11106717/); the same 87% / 94% are quoted in Dorkenwald et al. 2024 | high |
| Known cell types predicted correctly (FAFB-FlyWire): **acetylcholine 91%, glutamate 91%, GABA 96%, dopamine 90%, octopamine 85%, serotonin 33%** | Cell types whose transmitter is known from the literature (624 FAFB-FlyWire types in total; counts per transmitter not given in the text). | Eckstein et al. 2024 | high |
| Glutamate ↔ GABA is "our network's most common confusion" | Qualitative, from the test-set confusion matrix (Fig. 2A); the per-transmitter test numbers are only in the figure, which I could not read as text. | Eckstein et al. 2024 | high (statement); per-transmitter test numbers **not read** |
| Kenyon cells often predicted dopaminergic instead of cholinergic; some olfactory neurons serotonergic instead of cholinergic | Known systematic errors. | Eckstein et al. 2024 | high |
| **The connectivity file's sign and the annotations' `top_nt` disagree for 6,024 of 138,005 neurons (4.4%)** | *Our measurement.* Mapping `top_nt` from `neuron_annotations_v2.1.0.tsv` to a sign (acetylcholine, dopamine, serotonin, octopamine +; GABA, glutamate −) and comparing with the `Excitatory` column of `Connectivity_783.parquet`: 1,719 acetylcholine neurons are negative; 1,349 GABA and 2,943 glutamate neurons are positive. Why is not documented in either file; most likely a different prediction release or aggregation (per synapse vs per neuron). | this repository | high (the count); the cause is **unknown** |

**What this means for the model.** The model needs only a sign, so only some wrong predictions matter: acetylcholine ↔ GABA or glutamate flips a neuron; glutamate ↔ GABA (the commonest confusion) does not; dopamine, serotonin and octopamine count as excitatory (in the data, 5,897 of the 5,900 dopamine neurons that send connections are positive). So the per-neuron sign error is **at most about 6%** (100% − 94%) on the test set, probably less, but the share of that 6% that flips a sign is **not published**. The 4.4% disagreement between two signs derived from the same brain is a concrete, non-random second opinion.

## 4. Proofreading: merge and split errors

| Number | What exactly it measures | Source | How sure |
|---|---|---|---|
| **99.2% average F1 by volume** | 826 randomly chosen central brain neurons re-proofread by experts; the original against the re-proofread segment, by volume overlap. One example neuron scored 0.936. | Dorkenwald et al. 2024 | high |
| Merge and split rates separately | **Not published.** F1 by volume combines both, and weights them by volume, not by synapses. | — | high (read the relevant Methods) |
| Neuron counts left vs right differ by 42 (0.1%) for central brain intrinsic neurons; about 1 in 6 cell types differs in number between hemispheres | Partly biology, partly reconstruction. | Schlegel et al. preprint | medium |
| v783 required 3,013,513 edits (~33 person-years) | Proofreading effort, not an error rate. | Dorkenwald et al. 2024 | high |

**What this means for the model.** A split shows up as missing synapses on one neuron, correlated (a lost twig takes its synapses with it); a merge as another neuron's synapses attributed to it. There is no published rate to anchor either; only the 99.2% volume F1 bounds them, and unattached twigs (section 2) are the largest split-like loss.

## 5. Consistency between reconstructions (the best empirical "re-measurement")

| Number | What exactly it measures | Source | How sure |
|---|---|---|---|
| 53% of hemibrain connections also found in FlyWire; FlyWire left→right 57%, right→left 59% | All connections between matched cell types, any strength. | Schlegel et al. preprint | medium |
| A one-synapse hemibrain connection: 41% chance to appear in one FlyWire hemisphere, 14% in both | Weak connections are the unreliable ones. | Schlegel et al. preprint | medium |
| **Connections > 10 synapses or > 1% of the target's input are found again in > 90% of cases** | The paper's heuristic for a reliable connection (in the published abstract). | Schlegel, P. et al. 2024, *Nature* 634, 139–152 (abstract); numbers from the preprint | high (heuristic); medium (exact figures) |
| Connection weights correlate with Pearson R 0.96 within FlyWire (left vs right) and 0.81 across datasets | Edge weights between matched types. | Schlegel et al. preprint | medium |

These mix reconstruction errors with real differences between hemispheres and flies, so they are an *upper* bound on reconstruction error and a *lower* bound on "how different another real fly's connectome would be".

## What is not published (as far as this check found)

1. Precision and recall of the final FlyWire v783 synapse table.
2. Merge and split error rates separately, or per synapse.
3. Per-transmitter accuracy on the test set as text (only as a figure), and the share of wrong predictions that would flip an excitatory/inhibitory sign.
4. Why the `Excitatory` column and `top_nt` disagree for 4.4% of neurons.

The proposal ADR anchors its error rates on the numbers above and says, rate by rate, which are measured and which are bounds.

## Not yet checked

- The published (Nature) versions of the Schlegel et al. numbers in sections 2, 4 and 5 (read here from the bioRxiv preprint).
- Later work, if any, re-estimating FlyWire synapse accuracy (e.g. from the 2025–26 male CNS comparisons), and any robustness analysis in Shiu et al. 2024 itself (the preprint was not readable from here).
