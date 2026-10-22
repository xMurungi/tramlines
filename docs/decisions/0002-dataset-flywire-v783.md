# 0002 — The brain comes from FlyWire v783

- Status: Locked
- Date: 2026-10-22
- Phase: 0
- Decider: Owner

## Context
A brain emulation is only as real as its wiring. Several fly connectomes exist (FlyWire, the hemibrain, MaleCNS) and FlyWire itself has several versions (630, 783). Root IDs, the numbers that name each neuron, change between versions, so mixing versions silently breaks everything.

## Options considered
1. **FlyWire v630**: the version used in the original Shiu et al. paper. Matches the published figures exactly, but superseded.
2. **FlyWire v783**: the public release. Used by the Shiu model repository's updated config and by Eon Systems. Complete adult female brain, about 138,000 neurons.
3. **MaleCNS** (2026): brain plus nerve cord, newer, but no validated LIF model built on it yet. Kept for a Future Season.

## Decision
We use FlyWire v783 for the brain, and every neuron ID in this repository is a v783 root ID looked up from annotations, never typed in from elsewhere.

## Consequences
- We match the data Eon and the Shiu repository use today, so we can cross-check against them.
- Published figures in Shiu et al. used v630, so small numerical differences from the paper are expected. Phase 1 compares *qualitatively*.
- Any ID found in a blog post, paper or notebook must be checked against v783 before use. The Shiu example notebook itself uses v630 IDs (see [reference model notes](../science/reference-model-notes.md)).
- The exact files and download source are recorded in [ADR-0013](0013-data-files-and-source.md).

## For learners
A connectome is published in versions, like software. Each version renames some neurons, because proofreaders split and merge pieces of them. Using one version everywhere is how we make sure "neuron 720575940660219265" always means the same cell. Chapter 17 loads this data.
