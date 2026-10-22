# 0015 — Test conventions: data-gated tests and Book output files

- Status: Accepted (delegated)
- Date: 2026-10-22
- Phase: 0
- Decider: Claude (delegated)

## Context
Some tests need the 104 MB FlyWire files, which are not in git. Book code must be tested (CLAUDE.md 12.5), and the simplest honest test of a teaching program is "it prints exactly what the chapter says".

## Options considered
1. **Data tests carry a `data` marker and skip with a clear message when the files are absent; Book programs `book/chNN/name.py` sit next to `name.expected` holding their exact output.** Simple, readable by a beginner, no test framework magic inside the chapters.
2. **Download data inside the test run; parse expected output out of the chapter markdown.** Fewer files, but tests become slow and network-dependent, and markdown parsing is fragile.

## Decision
Option 1. `tests/test_data.py` skips if the data is missing; `tests/test_book.py` runs every `book/ch*/*.py` that has a matching `.expected` file and compares stdout exactly.

## Consequences
- A fresh clone passes `uv run pytest` before downloading data, with data tests shown as skipped (never silently).
- `uv run pytest -m data` runs only the data tests.
- Programs whose output is random or timing-dependent must print something stable (or set a seed), which is good teaching anyway.

## For learners
A test is a small program that checks another program. Here the rule is easy to remember: next to every Book program there is a text file with what it should print. If they ever stop matching, the build turns red.
