# 0017 — Annotation release v2.1.0, and the neurons of the sugar → MN9 test

- Status: Accepted (delegated). The annotation source and the Phase 3 sugar port are flagged for the owner ([owner decisions](../owner-decisions.md), items 2 and 3).
- Date: 2026-10-22
- Phase: 1
- Decider: Claude (delegated)

## Context
CLAUDE.md 7.1 says cell type annotations come from FlyWire Codex, with the exact release recorded, and that every ID is v783 and found from annotations. CLAUDE.md 7.3 says the sugar GRN set and MN9's ID come "from the reference code or annotations, not from memory".

What we found:

- **Codex** bulk downloads (`codex.flywire.ai/api/download`) return a login page without an account.
- **`flyconnectome/flywire_annotations`** is the published source of FlyWire's cell types (Schlegel et al. 2024). Its tag **v2.1.0** (2024-07-30) has 139,255 rows, all v783 root IDs, and contains **all 138,639** neurons of our brain. The newest tag, v3.2.0 (2026-09), lacks 14 of our neurons, so it has moved on from pure v783.
- **There is no "MN9" label** in the annotations. The reference MN9 (`720575940660219265`, from Shiu et al.'s notebook) is annotated `super_class = motor`, `cell_type = CB0701`, right side, pharyngeal nerve. CB0701 has exactly two neurons, one per side.
- **The annotations do not separate sugar from water GRNs** in v2.1.0: one class, `sugar/water`, with 67 neurons entering on the left and 64 on the right. The reference experiment's 21 sugar GRNs are all among the 67 left ones (type LB3, labial nerve). The reference notebook calls them right-hemisphere neurons; the annotations' `side` is the nerve-entry side. Early FlyWire releases were displayed mirrored, which may explain the mismatch; we have not verified that.

## Options considered
1. **Annotations v2.1.0 + the reference experiment's neuron sets, each checked against the annotations.** Reproduces exactly what Shiu et al. stimulated, with every ID verified as v783 and as the right cell class.
2. **Annotations only:** stimulate all 67 `sugar/water` GRNs on that side. Purely annotation-derived, but includes water-sensing neurons, so it is a different experiment from the published one.
3. **Codex export.** Needs an account, and is built from the same annotation data.
4. **Annotations v3.2.0** (newest, which splits sugar from water). No longer matches v783 exactly.

## Decision
Option 1 for the acceptance test, Option 2 run alongside as a robustness check.

- `scripts/fetch_data.py` fetches `Supplemental_file1_neuron_annotations.tsv` at tag v2.1.0 (commit `ebd66db2`), checked by SHA-256, saved as `data/neuron_annotations_v2.1.0.tsv`.
- `tramlines/brain/neurons.py` holds the 21 reference sugar GRNs (Eon's v783 version of Shiu et al.'s list) and the reference MN9, with their provenance. `tests/test_neurons.py` checks every one against the annotations.
- We record **both** CB0701 neurons and report the reference one as "MN9".

## Consequences
- The 21 IDs are the one place where IDs come from a list rather than an annotation query; CLAUDE.md 7.3 allows it, and the tests make a stale ID fail loudly.
- Which neurons "taste sugar" in the 2D world (Phase 3) is a separate, Reserved decision. The two options above are the starting point.
- If the owner prefers Codex, the swap touches only `fetch_data.py` and `neurons.py`.

## For learners
Scientists name neurons in layers: a broad class ("gustatory"), a sub-class ("sugar/water"), a type ("LB3"). Our code asks the annotation table for neurons by those names instead of trusting numbers copied from elsewhere. When we do copy numbers, from the reference experiment, a test checks each one against the table. Chapter 17 shows how to query the annotations.
