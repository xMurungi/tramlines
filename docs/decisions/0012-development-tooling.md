# 0012 — Development tooling: uv, Vite, MkDocs Material, pytest, ruff, mypy, git

- Status: Locked
- Date: 2026-10-22
- Phase: 0
- Decider: Owner

## Context
A beginner must be able to install everything in minutes, and the builder must be able to check every change automatically.

## Options considered
1. **uv, Vite, MkDocs Material, pytest, ruff, mypy, git.** Modern, fast, one command each, widely documented.
2. **conda/pip + webpack + Sphinx + flake8/black.** Older and well known, but slower and with more moving parts to teach.

## Decision
Python environments and dependencies are managed with uv; the frontend uses Vite; docs use MkDocs Material; tests use pytest; lint and format use ruff; types use mypy (`--strict` on `tramlines/`); history uses git.

## Consequences
- Versions installed in Phase 0 (2026-10-22): uv 0.13.5, Python 3.12.15, Vite 8.3, TypeScript 7.0, Node 22.22. Exact Python versions are in `uv.lock`; web versions in `web/package-lock.json`.
- One-command checks: `uv run pytest`, `uv run ruff check .`, `uv run mypy`, `uv run mkdocs serve`, `npm run build` in `web/`.
- Adding or swapping any of these is Reserved.

## For learners
Tools are how a project stays tidy as it grows. uv installs Python and its packages, pytest runs tests, ruff tidies the code, mypy checks types, and git remembers every version. Chapters 2 and 7 introduce uv and git.
