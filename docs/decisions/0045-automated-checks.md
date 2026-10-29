# 0045 — Automated checks on GitHub

- Status: Accepted (owner, 2026-10-24: "add the gh tests")
- Date: 2026-10-24
- Phase: 5
- Decider: Owner (setup delegated)

## Context
Every session ran the checks by hand and recorded them in each PR. With parallel agents and a growing test suite, that depends on every agent remembering. Two silent bugs this session (ADR-0038, ADR-0041) showed how much the tests are worth when they run every time.

## Options considered
1. **Fast checks on every PR, the full determinism gate on a schedule** (chosen). Lint, strict types, the whole test suite with the FlyWire data (downloaded once and cached, 125 MB, checksums verified), the strict docs build and the viewer build on every PR and push to develop; the 13-minute, 10-repeat gate weekly and on demand.
2. **Everything on every PR, gate included.** Strictest, but about 20 minutes per PR and many more of the private repository's free minutes.
3. **Small-network tests only, no data.** Fastest, but skips the full-brain tests that matter most.

## Decision
Option 1: `.github/workflows/checks.yml`, three jobs: `python` (ruff, mypy, pytest, mkdocs), `web` (TypeScript strict build), `determinism-gate` (Mondays 03:00 UTC, and by hand from the Actions tab). PyTorch installs from PyPI as locked (its Linux wheels bring GPU libraries, a few GB, cached after the first run); changing where PyTorch comes from would change the dependency setup, which is the owner's call.

## Consequences
- A PR shows a green tick or a red cross; the owner can require green before merging (GitHub: Settings → Branches → branch protection on `develop`).
- The tests now run on Linux as well as macOS. If a result differs between them, that is worth knowing; determinism is promised within one machine (L7), not across operating systems.
- Free minutes: a PR run is about 5–10 minutes (longer the first time), the weekly gate about 20, well inside the free allowance.

## For learners
Continuous integration means a robot runs your tests every time anyone proposes a change. It never forgets, never skips the slow test, and checks on a computer that is not yours, so "it works on my machine" stops being enough.

## Addendum (2026-10-24): CODEOWNERS and the branch rule
- `.github/CODEOWNERS` names xMurungi as owner of everything (owner's request). GitHub then requests the owner's review on pull requests opened by anyone else.
- A rule on `develop` that *requires* an approving review (or a code-owner review) cannot be met in a one-account repository, because nobody can approve their own pull request; every PR here is opened from the owner's account. The recommended rule for now: require the status checks "lint, types, tests, docs" and "viewer build (TypeScript strict)", with no required approvals. Turn approvals on once there are other contributors.

## Addendum (2026-10-29): studies in the cloud
`.github/workflows/run-study.yml` runs a chosen study on GitHub's machines, started by hand from the Actions tab, and returns its results as a downloadable artifact (owner's request: compute in the cloud instead of the laptop). Choices are fixed in the workflow (horizon, null brain, decoder-free, backward horizon, atlas, the slider precompute), inputs are validated, and the default is one worker because standard runners have little memory. Limits: the private repository's monthly free minutes and 6 hours per job. A rented large machine (16–32 cores, 32–64 GB) remains the option for the biggest studies; that needs the owner's own cloud account and billing.

