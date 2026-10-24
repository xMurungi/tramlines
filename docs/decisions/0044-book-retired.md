# 0044 — The Book is retired: the repository is the learning path

- Status: Accepted (owner, 2026-10-24). Supersedes [ADR-0011](0011-the-book.md) (locked decision L11).
- Date: 2026-10-24
- Phase: 5
- Decider: Owner

## Context
L11 promised a from-zero book ("someone who has never written Hello World can follow it") built alongside the code. Nine chapters exist (2, 17–22, 25, 26), each tested. The review in issue #14 suggested parking it; owner decision 20 asked about its scope. The owner's answer: "for the book it seems it will be a redundant thing and the project can be rebuilt with the guide of AI pointed to the repo that could just do the book for the person if they want to."

## Options considered
1. **Keep writing the full Book** (chapters 0–32). Pros: a finished teaching artefact. Cons: weeks of writing; every code change risks breaking a chapter; an AI assistant can now tailor such a path to each reader.
2. **Park it as a separate project** (the review's suggestion). Pros: keeps the option. Cons: an unfinished promise in the repository.
3. **Retire it** (chosen): keep the nine chapters as learning notes, stop writing new ones, and add a short guide for rebuilding the project with an AI assistant.

## Decision
The Book is no longer a deliverable. CLAUDE.md is amended: L11 superseded; the "every code change gets its chapter" rule and the Book in the Definition of Done and the phase endings are removed; section 12 is kept as history. The existing chapters stay (as "Learning notes") and their tests keep running while they pass; if code changes break one, it is removed rather than rewritten. New page: [Rebuild it with an AI assistant](../rebuild-with-ai.md). ADRs keep their "For learners" section: the decisions themselves are the teaching material.

## Consequences
- More time for the science and the experience.
- The learning path is now the repository: CLAUDE.md, the ADRs with "For learners", the journal and the honesty page.

## For learners
We set out to write a book that would teach anyone to build this project from zero. Partway through, it became clear that an AI assistant pointed at this repository can do that better for each reader, at their own pace. So we kept what was written as notes and put our effort where nothing can replace it: the experiments.
