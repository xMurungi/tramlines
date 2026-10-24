# 0043 — Licence: MIT for the code, CC BY 4.0 for the docs, figures and results

- Status: Accepted (owner delegated the choice on 2026-10-24: "add the appropriate licence")
- Date: 2026-10-24
- Phase: 5
- Decider: Claude (delegated by the owner; licensing is Reserved, CLAUDE.md 2.2)

## Context
The repository had no licence (owner decision 7). Without one, nobody else may legally reuse the code, which matters for a project meant to be shared and checked by scientists. Constraints: our dependencies are all permissive (PyTorch, NumPy and pandas: BSD; FastAPI, pydantic, MkDocs Material and Vite: MIT; pyarrow: Apache-2.0); the reference neuron model (Shiu et al.) is MIT; no code was copied from GPL projects (Eon's fly-brain is GPL-2.0-or-later, which is why we never borrowed from it); the FlyWire data is CC BY 4.0 and is downloaded, not bundled.

## Options considered
1. **MIT** for code. Shortest permissive licence, the norm in computational neuroscience, the same as the reference model. No explicit patent grant.
2. **Apache-2.0** for code. Permissive with an explicit patent grant and NOTICE rules. More formal than this project needs.
3. **GPL-3.0** for code. Forces derivatives to stay open, but blocks reuse inside many labs' and companies' code, and nothing here obliges it.
4. For the **text, figures and result data**, a code licence fits poorly. **CC BY 4.0** is the licence of the FlyWire data the results come from.

## Decision
Code under **MIT** (`LICENSE`); everything in `docs/` (text, figures, result data) and the learning notes in `book/` under **CC BY 4.0** (`LICENSE-docs.md`). Copyright "xMurungi and Tramlines contributors" (no personal name, by the owner's privacy rule). Declared in `pyproject.toml` and `web/package.json`.

## Consequences
- Anyone may reuse, change and redistribute the code with the copyright notice, and the results with credit.
- Third-party material keeps its own terms: the FlyWire data (CC BY 4.0, credited per `docs/science/citations.md`), the VFB template (not bundled).
- Choosing a licence does not publish anything: the repository stays private until the owner decides on release (Phase 8).

## For learners
A licence is the permission slip that comes with code. With no licence, the default is "all rights reserved", so even a public repository cannot legally be reused. MIT says "do what you like, keep our name on it"; CC BY says the same for writing and pictures. We matched the licences of the work we build on: the neuron model's code is MIT, and the fly's wiring data is CC BY.
