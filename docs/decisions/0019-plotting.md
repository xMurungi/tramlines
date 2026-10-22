# 0019 — matplotlib for figures, in an optional dependency group

- Status: Accepted (delegated)
- Date: 2026-10-22
- Phase: 1
- Decider: Claude (delegated; CLAUDE.md 2.1 lists plotting library details as delegated)

## Context
The Phase 1 gate needs a committed plot (CLAUDE.md 7.3). Figures for the docs are static images; the live viewer is a separate TypeScript app.

## Options considered
1. **matplotlib**, in a separate `analysis` dependency group. The standard scientific plotting library, writes PNG/SVG, no browser needed.
2. **Plotly / Bokeh.** Interactive, but heavier, and the docs only need still images.
3. **Hand-written SVG.** No dependency, but slow to write and hard to teach.

## Decision
matplotlib, in the `analysis` group (installed by default with `uv sync`, not needed by the engine itself). Figures use the project's dark surface (`#07070a`). Two-series figures use gold `#bb861f` and blue `#3a9fc4`, a pair that passes a colour-vision check on the dark surface: lightness band, chroma, colour-blind separation (ΔE 20.5) and contrast. Every series is also labelled directly, so colour is never the only cue.

## Consequences
- The engine package (`tramlines/`) does not import matplotlib.
- The brighter gold `#e8b04a` in `web/src/styles/tokens.css` is for the live fly. Figures use the slightly darker step for legibility.

## For learners
A plot is a tool for seeing, not decoration. We pick colours that people with colour-blindness can tell apart, and we write labels on the lines themselves, so nobody has to match colours to a legend. Chapter 18 makes the first plot.
