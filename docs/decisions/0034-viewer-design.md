# 0034 — The viewer's look: fonts, a single dark theme, and what each mark means

- Status: Accepted (delegated; CLAUDE.md 9.4 asks for the fonts to be chosen in an ADR)
- Date: 2026-10-23
- Phase: 4
- Decider: Claude (delegated)

## Context
CLAUDE.md 9 sets the mood (sacred, silent, golden, inevitable), the palette (void, gold, ghost, restrained branch hues, one electric accent) and the screen composition, and asks for one serif display face and one monospace face, chosen from Google Fonts in an ADR.

## Options considered
1. **Cormorant Garamond (display) + JetBrains Mono (everything else).** A high-contrast, calm serif used only for the name, and a clear monospace for all numbers and labels, so the screen reads like an instrument.
2. **A geometric sans for everything.** Clean, but loses the "sacred machine" contrast the brief asks for.
3. **A slab or grotesque display face.** Stronger, but louder than "silent".

## Decision
Option 1, and these meanings, used the same way everywhere:

| Mark | Meaning |
|---|---|
| Solid gold fly and trail | the live fly (the timeline on screen) |
| Dotted gold line, faint blurred gold fly | the ghost: an independent prediction, 3 s ahead |
| Solid pale ring / dashed violet ring | food / bitter (a laced patch shows both; fainter = weaker) |
| Dark wedge from the dish's edge | a looming shadow, growing as it arrives |
| Gold points in the brain panel | neurons that fired in the current 100 ms |
| Electric cyan | the match meter and the free-will button: the only accent |

- **Single dark theme by design:** the viewer is the machine's room; it does not follow the system's light mode. Every colour is a token in `web/src/styles/tokens.css`.
- `prefers-reduced-motion` turns off the ghost's blur.

## Consequences
- The lab notes page and documentation figures use the same gold and dark ground, so screenshots, figures and the viewer look like one thing.
- Branch hues for Phase 5 are still to choose: desaturated, never rainbow (CLAUDE.md 9.2).

## For learners
On a screen like this, every colour has one job. Gold means "what is happening", faint gold means "what will happen", and cyan means "the machine checking itself". If you keep those jobs fixed, people learn to read the screen in seconds. Chapter 29 draws it.
