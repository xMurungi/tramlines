# 0011 — The repository ships The Book

- Status: Locked
- Date: 2026-10-22
- Phase: 0
- Decider: Owner

## Context
The owner wants someone who has never written a line of code to be able to build this exact project and understand every part. Documentation written at the end is usually thin and out of date.

## Options considered
1. **A from-zero book, written alongside the code, with every code block tested in CI.** Expensive, but always true, and a product in its own right.
2. **Developer docs only** (API reference, architecture notes). Cheaper, useless to a beginner.
3. **A separate tutorial written after v1.** Risks never being written and drifting from the code.

## Decision
The repository contains The Book (`docs/book/` for prose, `book/chNN/` for runnable code), written alongside each phase and tested by `tests/test_book.py`.

## Consequences
- Every phase ends with its chapters written and their code passing tests.
- Code must be explainable; clever code that cannot be taught is a cost.
- Chapters the owner marks as reviewed are not rewritten without permission.

## For learners
You are reading part of this decision right now. The Book is built to make the path gentle, not the project small: you will build the real thing. Each chapter's code is run automatically, so if the book says a program prints something, it does.
