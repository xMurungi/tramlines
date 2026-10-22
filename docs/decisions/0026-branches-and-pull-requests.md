# 0026 — Every change arrives through a pull request into `develop`

- Status: Accepted (owner request, workflow details delegated)
- Date: 2026-10-22
- Phase: 3
- Decider: Owner (asked for PRs merged into `develop`); details by Claude (delegated)

## Context
Until session 4, commits went straight to `develop` and were pushed. The owner asked for pull requests merged into `develop` instead, so every change has one reviewable page on GitHub (`github.com/xMurungi/tramlines`, private).

## Options considered
1. **One branch and one PR per coherent piece of work, merged with a merge commit after local checks pass.** Keeps the small commits CLAUDE.md 13.4 asks for, and gives each change a summary page.
2. **Squash-merge each PR.** A tidier history, but loses the small commits and their ADR references.
3. **Keep pushing to `develop`.** Fastest, but no review page, and not what the owner asked for.

## Decision
Option 1.

- **Branch names:** `<area>/<topic>`, using the commit-message areas (`brain/`, `world/`, `tests/`, `book/`, `docs/`, `data/`, `science/`), e.g. `world/senses`.
- **Before opening a PR:** the every-change checks pass locally: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run mkdocs build --strict`, plus `npm run build` if `web/` changed. Any change to the engine or timeline also runs the determinism gate (`TRAMLINES_DETERMINISM_REPEATS=10`).
- **Privacy check** on the diff before pushing: nothing personal except the GitHub handle (session 4 rule).
- **PR description:** what changed and why, the checks run with their results, linked ADRs, anything waiting on the owner.
- **Merge:** `gh pr merge --merge --delete-branch`, then pull `develop`. The builder merges its own PRs once checks pass, as the owner asked; the owner can review any PR, before or after.
- **Outside a PR:** nothing, except history repairs the owner explicitly requests.

## Consequences
- There is no CI on GitHub yet, so "checks pass" means locally, recorded in each PR description. A GitHub Actions workflow would run them on GitHub too; adding one is listed for the owner (it touches the toolchain, CLAUDE.md 2.2).
- Session-4 work before this ADR was pushed directly; it is not re-opened as PRs.

## For learners
A pull request is a proposal to change the shared code: "here is my branch, here is what it does, here is proof it works". Even when one person writes and merges, PRs leave a readable trail of *why* each change happened. Chapter 7 introduces branches; Chapter 31 covers shipping.
