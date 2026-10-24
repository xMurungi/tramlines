# Rebuild it with an AI assistant

The Book was retired ([ADR-0044](decisions/0044-book-retired.md)). This repository is the learning path, and an AI coding assistant can guide you through it at your own pace, from your first line of Python to the whole machine.

## How
1. Get the repository, and open an AI coding assistant at its root.
2. Ask it to read, in this order: `CLAUDE.md` (what the project is and how it is built), `ROADMAP.md` (the phases), [the decision records](decisions/index.md) (every choice and why, each with a "For learners" section), [the journal](journal/2026-10-24-session-9.md) and the [honesty page](honesty.md).
3. Tell it where you are starting from, and what you want to build.

## Prompts that work
- "I have never programmed. Teach me enough Python to understand `tramlines/brain/params.py`, one small step at a time, with something I can run at each step."
- "Walk me through Phase 1: build a single leaky integrate-and-fire neuron, then two, then load FlyWire and reproduce the sugar → MN9 result. Stop after each step so I can run it."
- "Explain ADR-0022 (the sacred tests) and help me write my own bit-exact fork test."
- "Rebuild Result 1 with me: what imperfect knowledge means, and how the horizon study measures it."

## Learning notes
Chapters written before the Book was retired are kept under **Learning notes** in the navigation; their code lives in `book/` and is tested.
