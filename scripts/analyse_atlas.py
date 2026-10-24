"""Result 3's analysis, exactly as pre-registered (docs/science/atlas-plan.md).

Reads docs/assets/atlas_{screen,outcomes,decoder}.csv; computes E1-E4 and judges H1-H5
by their stated criteria; writes docs/assets/atlas_summary.csv and atlas.png.

    uv run python scripts/analyse_atlas.py
"""

from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path

import numpy as np

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
MOMENTS = [250, 750, 1250, 1750, 2250, 2750, 3250, 3750]
GROUPS = ["random", "awake", "inputs"]
Row = dict[str, str]


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    z, p = 1.959964, k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, c - h), min(1.0, c + h)


def fmt(k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"{k}/{n} [{lo:.1%}-{hi:.1%}]"


def load(name: str) -> list[Row]:
    return list(csv.DictReader((ASSETS / f"atlas_{name}.csv").open()))


def is_true(row: Row, key: str) -> bool:
    return row[key] == "True"


def change_rate(screen: list[Row], follow: list[Row], cells: set[tuple[str, str]]) -> float:
    """E2 for a set of cells: P(c)P(change|c) + P(no c)P(change|no c), random group."""
    total = 0.0
    for cell in cells:
        s = [r for r in screen if (r["seed"], r["moment_ms"]) == cell and r["made"] == "True"]
        f = [r for r in follow if (r["seed"], r["moment_ms"]) == cell and r["made"] == "True"]
        if not s:
            continue
        pc = sum(int(r["spike_differences"]) > 0 for r in s) / len(s)
        fc = [r for r in f if is_true(r, "cascade")]
        fn = [r for r in f if not is_true(r, "cascade")]
        qc = sum(is_true(r, "choice_differs") for r in fc) / len(fc) if fc else 0.0
        qn = sum(is_true(r, "choice_differs") for r in fn) / len(fn) if fn else 0.0
        total += pc * qc + (1 - pc) * qn
    return total / len(cells)


def e2_with_ci(screen: list[Row], follow: list[Row], cells: list[tuple[str, str]]) -> str:
    """Stratified bootstrap (10,000 resamples, seed 0) within each cell's screen and follow-ups."""
    rng = np.random.default_rng(0)
    point = change_rate(screen, follow, set(cells))
    by_cell = {}
    for cell in cells:
        s = [int(int(r["spike_differences"]) > 0) for r in screen
             if (r["seed"], r["moment_ms"]) == cell and r["made"] == "True"]  # fmt: skip
        f = [r for r in follow if (r["seed"], r["moment_ms"]) == cell and r["made"] == "True"]
        fc = [int(is_true(r, "choice_differs")) for r in f if is_true(r, "cascade")]
        fn = [int(is_true(r, "choice_differs")) for r in f if not is_true(r, "cascade")]
        by_cell[cell] = (np.array(s), np.array(fc or [0]), np.array(fn or [0]))
    boots = np.zeros(10_000)
    for s_arr, fc_arr, fn_arr in by_cell.values():
        pc = rng.choice(s_arr, (10_000, len(s_arr))).mean(1)
        qc = rng.choice(fc_arr, (10_000, len(fc_arr))).mean(1)
        qn = rng.choice(fn_arr, (10_000, len(fn_arr))).mean(1)
        boots += pc * qc + (1 - pc) * qn
    boots /= len(by_cell)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return f"{point:.2%} [{lo:.2%}-{hi:.2%}]"


def analyse(screen: list[Row], follow: list[Row], rerun: list[Row], label: str) -> list[str]:
    out = [f"== {label}"]
    made_s = [r for r in screen if r["made"] == "True"]
    not_made = len(screen) - len(made_s)
    out.append(f"screened {len(screen)}, made {len(made_s)}, not made {not_made}")

    # E1 / H1: cascade rate per group and moment
    h1_ok = True
    for g in GROUPS:
        cells = []
        for m in MOMENTS:
            rows = [r for r in made_s if r["group"] == g and int(r["moment_ms"]) == m]
            k = sum(int(r["spike_differences"]) > 0 for r in rows)
            cells.append(f"{m}:{fmt(k, len(rows))}")
            if g == "random" and rows and k / len(rows) > 0.15:
                h1_ok = False
        out.append(f"E1 cascade {g}: " + "  ".join(cells))
    out.append(f"H1 most spikes die (random <= 15% at every moment): "
               f"{'SUPPORTED' if h1_ok else 'NOT SUPPORTED'}")  # fmt: skip

    # E2: random-spike choice-change rate, per moment and pooled
    rnd_s = [r for r in screen if r["group"] == "random"]
    rnd_f = [r for r in follow if r["group"] == "random"]
    seeds = sorted({r["seed"] for r in screen})
    for m in MOMENTS:
        moment_cells = [(s, str(m)) for s in seeds]
        rate = e2_with_ci(rnd_s, rnd_f, moment_cells)
        out.append(f"E2 random spike changes the choice, {m} ms: {rate}")
    all_cells = sorted({(r["seed"], r["moment_ms"]) for r in screen})
    out.append(f"E2 pooled: {e2_with_ci(rnd_s, rnd_f, all_cells)}")

    # H2: screen misses little
    quiet = [r for r in follow if r["made"] == "True" and not is_true(r, "cascade")]
    kq = sum(is_true(r, "choice_differs") for r in quiet)
    out.append(f"H2 screen misses little (<= 5% change choice): {fmt(kq, len(quiet))} "
               f"-> {'SUPPORTED' if kq / len(quiet) <= 0.05 else 'NOT SUPPORTED'}")  # fmt: skip

    # H3: inputs cascade more than random
    def pooled(g: str) -> tuple[int, int]:
        rows = [r for r in made_s if r["group"] == g]
        return sum(int(r["spike_differences"]) > 0 for r in rows), len(rows)

    ki, ni = pooled("inputs")
    kr, nr = pooled("random")
    ok = wilson(ki, ni)[0] > wilson(kr, nr)[1]
    out.append(f"H3 aiming works: inputs {fmt(ki, ni)} vs random {fmt(kr, nr)} -> "
               f"{'SUPPORTED' if ok else 'NOT SUPPORTED'}")  # fmt: skip

    # H4: many brain futures, one behaviour
    casc = [r for r in follow if r["made"] == "True" and is_true(r, "cascade")]
    ks = sum(not is_true(r, "choice_differs") for r in casc)
    out.append(f"H4 cascades leaving the choice unchanged (>= 50%): {fmt(ks, len(casc))} -> "
               f"{'SUPPORTED' if ks / len(casc) >= 0.5 else 'NOT SUPPORTED'}")  # fmt: skip
    kp = sum(r["path_wrong_from_ms"] != "" for r in casc)
    kb = sum(is_true(r, "behaviour_differs") for r in casc)
    out.append(f"   (secondary) cascades changing the path: {fmt(kp, len(casc))}; "
               f"behaviour incl. timing: {fmt(kb, len(casc))}")  # fmt: skip

    # E4 / H5: decoder robustness
    for v in sorted({r["variant"] for r in rerun}):
        tip = [
            r
            for r in rerun
            if r["variant"] == v and is_true(r, "tipping_by_default") and r["made"] == "True"
        ]
        ctl = [
            r
            for r in rerun
            if r["variant"] == v and not is_true(r, "tipping_by_default") and r["made"] == "True"
        ]
        kt = sum(is_true(r, "choice_differs") for r in tip)
        kc = sum(is_true(r, "choice_differs") for r in ctl)
        out.append(f"H5 {v}: tipping points survive {fmt(kt, len(tip))} -> "
                   f"{'SUPPORTED' if tip and kt / len(tip) >= 0.7 else 'NOT SUPPORTED'}; "
                   f"controls becoming tipping {fmt(kc, len(ctl))}")  # fmt: skip
    return out


def where(screen: list[Row], follow: list[Row]) -> list[str]:
    """E3: classes of random-group neurons that cascade and that change the choice."""
    from tramlines.brain.neurons import load_catalog

    cat = load_catalog()
    ann = cat.annotations
    roots = cat.root_ids

    def cls(i: str) -> str:
        root = int(roots[int(i)])
        return str(ann.loc[root, "super_class"]) if root in ann.index else "unknown"

    out = ["== E3 where (random group)"]
    rnd = [r for r in screen if r["group"] == "random" and r["made"] == "True"]
    base = Counter(cls(r["neuron"]) for r in rnd)
    casc = Counter(cls(r["neuron"]) for r in rnd if int(r["spike_differences"]) > 0)
    tip = Counter(
        cls(r["neuron"]) for r in follow if r["group"] == "random" and is_true(r, "choice_differs")
    )
    for c, n in base.most_common():
        out.append(
            f"  {c:28} screened {n:6}  cascade {fmt(casc[c], n)}  choice-changers followed {tip[c]}"
        )
    return out


def main() -> None:
    screen, follow, rerun = load("screen"), load("outcomes"), load("decoder")
    lines = analyse(screen, follow, rerun, "all seeds")

    def keep(rows: list[Row]) -> list[Row]:
        return [r for r in rows if r["seed"] != "0"]

    lines += analyse(keep(screen), keep(follow), keep(rerun), "seeds 1-2")
    lines += where(screen, follow)
    (ASSETS / "atlas_summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
