# Everything accessed, used and downloaded

A record, for the owner's review, of every outside resource the builder touched: what was installed on this machine, what was downloaded, which websites and services were contacted, and what was written outside the repository. Kept current every session.

Last updated: 2026-10-22 (session 6).

Personal details (the owner's name, machine, username, local paths) are deliberately left out of this page and the whole repository. Paths below are written relative to the home folder or as placeholders.

## 1. Software installed on this machine

| What | Version | How | Where it lives | Why |
|---|---|---|---|---|
| uv | 0.13.5 | `brew install uv` (Homebrew) | `/opt/homebrew/bin/uv` | Required by ADR-0012; was not installed. |
| Python | 3.12.15 | `uv python install 3.12` | `~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/` | ADR-0004 (system Python was 3.9.6). |
| Project Python packages | numpy 2.5.4, pandas 3.1.0, pyarrow 26.0.0, torch 2.14.1, matplotlib 3.11.2, mypy 2.4.0, pandas-stubs 3.0.5, pytest 9.1.1, ruff 0.17.1, mkdocs-material 9.7.7 (plus their dependencies) | `uv sync` from PyPI | `.venv/` in the project (git-ignored); exact versions in `uv.lock` | The project itself. |
| Web packages | vite 8.3.5, typescript 7.0.2 | `npm install` from the npm registry | `web/node_modules/` (git-ignored); exact versions in `web/package-lock.json` | Viewer skeleton (ADR-0005, ADR-0012). |

Side effects of the above: the uv download cache at `~/.cache/uv` (1.1 GB, reusable, safe to delete with `uv cache clean`), and matplotlib's font cache at `~/.matplotlib`.

Already present and used, not installed: git (`/usr/bin/git`), Node.js 22.22.3 (nvm), Homebrew, Xcode command-line tools.

## 2. Data downloaded

### Into the project (`data/`, git-ignored, checksums in `data/MANIFEST.md`)

| File | Source | Licence |
|---|---|---|
| `Completeness_783.csv` | `raw.githubusercontent.com/philshiu/Drosophila_brain_model` @ `91bdd1e7` | FlyWire data, CC BY 4.0 |
| `Connectivity_783.parquet` | same | CC BY 4.0 |
| `neuron_annotations_v2.1.0.tsv` | `raw.githubusercontent.com/flyconnectome/flywire_annotations` @ tag v2.1.0 (`ebd66db2`) | CC BY 4.0 |

### Into the session scratchpad (temporary, outside the project, never committed)

Scratchpad: a session-specific temporary folder under `/private/tmp/` (macOS clears it, or delete it by hand).

| What | Size | Why |
|---|---|---|
| Clone of `github.com/eonsystemspbc/fly-brain` @ `a3db62f9` (GPL-2.0-or-later) | ~380 MB (includes their data copies) | Studied for the reference notes. **No code copied** (licence). |
| Clone of `github.com/philshiu/Drosophila_brain_model` @ `91bdd1e7` (MIT) | ~80 MB | The reference model. Its `model.py` was *run* (unmodified, from the clone) under Brian2 for the full-brain cross-check. Its saved example results (`results/example/*.parquet`) were read for comparison. |
| `flywire_annotations` v3.2.0 neuron annotations (latest) | 32 MB | Compared with v2.1.0; rejected (no longer exactly v783). |
| `flywire_annotations` v2.1.0 neuron annotations | 27 MB | First copy, before adding it to `fetch_data.py`. |
| Codex download probe | 38 KB | Response was an HTML login page; this is how we learned Codex needs an account. |
| Brian2 environment `b2env/`: brian2 2.10.1, sympy 1.14.0, cython 3.1.3, joblib 1.6.0, setuptools 84.2.1, numpy, pandas, pyarrow | 290 MB | Running the reference simulator to verify our engine (ADR-0016). Not a project dependency. |
| Brian2 outputs, probe and comparison scripts, experiment logs | ~4 MB | Verification evidence summarised in ADR-0016 and ADR-0020. |

Also: `uv run --with brian2` built a throwaway Brian2 environment (in the uv cache) to generate `tests/golden/*.npz`.

## 3. Websites and services contacted

| Service | What for | Data sent |
|---|---|---|
| github.com (git over HTTPS) | Cloning the two reference repositories; **pushing this project to `github.com/xMurungi/tramlines`, branch `develop`** (owner's instruction, session 3) | The project's git history (no data files). |
| api.github.com (unauthenticated REST) | Latest commit, tags, releases and file listing of `flyconnectome/flywire_annotations` | None beyond the request. |
| raw.githubusercontent.com | Downloading the data files above | None. |
| Local system tools only (`top`, `ps`, `sysctl`, `pmset`, `memory_pressure`) | Monitoring the machine during experiments (session 6); no network, no admin rights | None. |
| codex.flywire.ai | One request to `/api/download?data_product=classification&data_version=783` | None (no login). |
| PyPI, npm registry, Homebrew, python-build-standalone (via uv) | Installing the software above, and running `git-filter-repo` once via `uvx` (session 4) | None. |

No accounts were created, no credentials were used except git's existing GitHub login for the push, and nothing was posted anywhere else.

In session 4, at the owner's request, `develop`'s history was rewritten with `git-filter-repo` to remove personal details that had been written into earlier commits, and force-pushed. Commit authors were already the GitHub handle with GitHub's private noreply email.

## 4. Written outside the repository

| Path | What |
|---|---|
| Claude Code's per-project memory folder under `~/.claude/projects/` | The builder's notes between sessions: pending owner decisions belong in `docs/owner-decisions.md`; never write the owner's personal details into the repository. Plus an index. |
| `.private/machine.md` in the project (git-ignored, never pushed) | The reference machine's specs for the performance budget, kept off GitHub. |
| `.private/bin/thermal_state` (+ its `.swift` source), git-ignored | A tiny helper compiled with the already-installed Xcode tools (`swiftc`) that prints macOS's thermal-pressure level for `scripts/monitor_system.py` (session 6). |
| `.private/monitoring/*.csv`, git-ignored | CPU, memory, swap and thermal readings taken while experiments ran (session 6). Read locally only; summaries without machine details are in ADR-0029. |
| The scratchpad above | Temporary files listed in section 2. |

## 5. Third-party material inside the repository

| What | Origin | Licence / note |
|---|---|---|
| 21 sugar GRN root IDs and the MN9 root ID (`tramlines/brain/neurons.py`, `book/ch18/wake_up.py`) | Shiu et al. example notebook (MIT) and Eon's v783 version of that list | Data identifiers, with provenance in ADR-0017. |
| Model equations and parameter values | Shiu et al. `model.py` (MIT) | Re-implemented, not copied (ADR-0016). |
| `tests/golden/*.npz` | Generated by us with Brian2 (CeCILL licence) | Outputs of a run, not Brian2 code. |
