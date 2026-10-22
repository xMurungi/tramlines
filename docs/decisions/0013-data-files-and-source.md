# 0013 — The v783 files are fetched from the Shiu repository at a pinned commit

- Status: Accepted (delegated)
- Date: 2026-10-22
- Phase: 0
- Decider: Claude (delegated)

## Context
CLAUDE.md section 7.1 expects two files, named as in Eon's repository (`2025_Completeness_783.csv`, `2025_Connectivity_783.parquet`), and asks us to verify the names, columns and download source. In Phase 0 we cloned both reference repositories and compared them:

- `Connectivity_783.parquet` (Shiu) and `2025_Connectivity_783.parquet` (Eon) are **byte-identical** (SHA-256 `efeb23fb…0347`).
- The two completeness CSVs differ only in line endings (Eon's copy has Windows `\r\n`). Same 138,639 root IDs, same order, same values.
- Eon's names are renames of Shiu's files. Shiu's repository is where they were first published, by the authors of the model.

This is a choice of *download source* for the same dataset version, not a change of dataset ([ADR-0002](0002-dataset-flywire-v783.md) is untouched).

## Options considered
1. **Shiu repository, pinned to commit `91bdd1e7`.** The model's own authors, MIT-licensed code repository, files unchanged since 2024. Raw GitHub URLs serve both files directly (no Git LFS).
2. **Eon repository, pinned commit.** Matches the names in CLAUDE.md, but the CSV has altered line endings, and the repository is an active benchmark project (GPL-2.0-or-later code).
3. **Rebuild from the FlyWire Zenodo release** (raw connections + neurotransmitter predictions). The most upstream source, but we would have to re-derive Shiu's sign rule and index columns ourselves, which is exactly where silent errors creep in. Worth doing later as a cross-check, not as the source.

## Decision
`scripts/fetch_data.py` downloads `Completeness_783.csv` and `Connectivity_783.parquet` from `raw.githubusercontent.com/philshiu/Drosophila_brain_model/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960/` and verifies each against a SHA-256 recorded in the script and in `data/MANIFEST.md`. We keep the upstream file names.

## Consequences
- Downloads are reproducible: the commit is fixed and the hash is checked; a mismatched download is discarded.
- Our file names differ from the `2025_…` names in CLAUDE.md section 7.1. The content is identical; if the owner prefers Eon's names, renaming is a one-line change.
- The loader checks on every load that index columns and root ID columns agree.
- Measured contents (recorded in `data/MANIFEST.md`): 138,639 neurons; 15,091,983 connections (distinct pre→post pairs, no self-loops, no duplicates); 54,492,922 synapses; 9,059,302 excitatory and 6,032,681 inhibitory connections.
- Cell type annotations (needed in Phase 1 to find sugar GRNs and MN9) are a separate source still to be chosen and recorded.

## For learners
When you download scientific data, write down *exactly* where it came from and a fingerprint of the file (a hash). Then anyone, years later, can check they have the very same bytes you used. Chapter 17 walks through `fetch_data.py` and what a SHA-256 hash is.
