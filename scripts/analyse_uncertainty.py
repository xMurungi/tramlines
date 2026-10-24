"""Uncertainty for Results 1 and 2, from their existing data only (no simulation).

Every count in ADR-0038's and ADR-0039's tables gets a Wilson 95% interval, and every
median they quote gets a bootstrap 95% interval (10,000 resamples, seed 0), both
computed exactly as Result 4 does (scripts/analyse_backward_horizon.py). The measures
are the ADRs' own, unchanged:

- Result 1 (ADR-0038): a ghost is "right" when its path stays within 0.1 mm for all
  3 s (`path_stays_right_ms == 3000` in horizon_v2.csv); a failed ghost's time is
  `path_stays_right_ms`. Walking "missed spike" has 6 made ghosts (ADR-0038 correction).
- Result 2 (ADR-0039): behaviour is judged by the cut-offs of scripts/plot_null_brain.py
  (walks > 10 mm in the arena; feeds/refuses by feeding_ms; escapes by jumps; stays
  quiet below 3,000 active neurons; held in place, a readout behaves when it fires).

The findings also compare counts ("timing matters", "the subtle decision breaks
first"). For each comparison the script gives the Newcombe 95% interval for the
difference of two proportions (hybrid Wilson score, method 10 of Newcombe 1998): a
difference is supported when that interval excludes zero.

Writes docs/assets/uncertainty_results_1_2.csv.

    uv run python scripts/analyse_uncertainty.py
"""

from __future__ import annotations

import csv
import math
from collections.abc import Callable
from pathlib import Path

import numpy as np

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
Z = 1.959964
RESAMPLES = 10_000
Row = dict[str, str]
Out = dict[str, str]
FIELDS = ["result", "table", "row", "column", "measure", "k", "n", "estimate", "low", "high",
          "shown_as"]  # fmt: skip


def interval(k: int, n: int) -> tuple[float, float]:
    """Wilson 95% interval for k successes out of n (as in analyse_backward_horizon)."""
    p = k / n
    centre = (p + Z * Z / (2 * n)) / (1 + Z * Z / n)
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / (1 + Z * Z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def wilson(k: int, n: int) -> str:
    """k/n with its Wilson 95% interval."""
    if n == 0:
        return "0/0"
    low, high = interval(k, n)
    return f"{k}/{n} [{low:.0%}-{high:.0%}]"


def bootstrap_median(values: list[float]) -> tuple[float, float, float]:
    """Median with a bootstrap 95% interval (10,000 resamples, seed 0)."""
    rng = np.random.default_rng(0)
    data = np.array(values, dtype=float)
    boots = np.median(rng.choice(data, (RESAMPLES, len(data))), axis=1)
    low, high = np.percentile(boots, [2.5, 97.5])
    return float(np.median(data)), float(low), float(high)


def newcombe(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float, float]:
    """p1 - p2 with the Newcombe (hybrid Wilson score) 95% interval."""
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = interval(k1, n1)
    l2, u2 = interval(k2, n2)
    d = p1 - p2
    low = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    high = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return d, low, high


def count(result: str, table: str, row: str, column: str, k: int, n: int) -> Out:
    low, high = interval(k, n)
    return {"result": result, "table": table, "row": row, "column": column,
            "measure": "count (Wilson 95%)", "k": str(k), "n": str(n),
            "estimate": f"{k / n:.4f}", "low": f"{low:.4f}", "high": f"{high:.4f}",
            "shown_as": wilson(k, n)}  # fmt: skip


def median(result: str, table: str, row: str, column: str, values: list[float], unit: str) -> Out:
    m, low, high = bootstrap_median(values)
    return {"result": result, "table": table, "row": row, "column": column,
            "measure": f"median {unit} (bootstrap 95%)", "k": "", "n": str(len(values)),
            "estimate": f"{m:g}", "low": f"{low:g}", "high": f"{high:g}",
            "shown_as": f"{m:g} [{low:g}-{high:g}] (n={len(values)})"}  # fmt: skip


def difference(result: str, claim: str, a: tuple[str, int, int], b: tuple[str, int, int]) -> Out:
    (name_a, k1, n1), (name_b, k2, n2) = a, b
    d, low, high = newcombe(k1, n1, k2, n2)
    verdict = "supported" if low > 0 or high < 0 else "NOT supported (interval includes 0)"
    return {"result": result, "table": "comparisons", "row": claim,
            "column": f"{name_a} minus {name_b}", "measure": "difference (Newcombe 95%)",
            "k": f"{k1}/{n1} vs {k2}/{n2}", "n": str(n1 + n2), "estimate": f"{d:.4f}",
            "low": f"{low:.4f}", "high": f"{high:.4f}",
            "shown_as": f"{wilson(k1, n1)} vs {wilson(k2, n2)}: {d:+.0%} "
                        f"[{low:+.0%} to {high:+.0%}], {verdict}"}  # fmt: skip


# --- Result 1 (ADR-0038) -------------------------------------------------------------

R1 = "1 (ADR-0038)"
MOMENTS = ["walking", "laced food", "shadow"]
GHOST_ROWS = [
    ("everything (control)", "everything (control)"),
    ("float32 precision", "float32 precision"),
    ("voltage to 0.001 mV", "voltage known to 0.001 mV"),
    ("voltage to 0.01 mV", "voltage known to 0.01 mV"),
    ("voltage to 0.03 mV", "voltage known to 0.03 mV"),
    ("voltage to 0.1 mV", "voltage known to 0.1 mV"),
    ("voltage to 1 mV", "voltage known to 1 mV"),
    ("one in-flight spike missed", "one in-flight spike missed"),
    ("99.9% of neurons", "99.9% of neurons observed"),
    ("99.5% of neurons", "99.5% of neurons observed"),
    ("99.0% of neurons", "99.0% of neurons observed"),
]
FULL_MS = 3_000


def ghosts(rows: list[Row], knows: str, moments: list[str]) -> tuple[int, int, list[float]]:
    """(right for all 3 s, made, failure times in ms) for one kind of ghost."""
    mine = [r for r in rows if r["ghost_knows"] == knows and r["moment"] in moments]
    times = [float(r["path_stays_right_ms"]) for r in mine]
    return sum(t == FULL_MS for t in times), len(mine), [t for t in times if t < FULL_MS]


def result_1(rows: list[Row]) -> list[Out]:
    out: list[Out] = []
    table = "findings (ghosts right for all 3 s)"
    all_failures: list[float] = []
    for label, knows in GHOST_ROWS:
        for moment in MOMENTS:
            k, n, failures = ghosts(rows, knows, [moment])
            if n == 0:
                continue
            out.append(count(R1, table, label, moment, k, n))
            all_failures += failures
            if len(failures) >= 2:
                out.append(median(R1, "time to fail", label, moment, failures, "ms"))
    out.append(median(R1, "time to fail", "every failed ghost", "all moments", all_failures,
                      "ms"))  # fmt: skip

    def pooled(label: str, knows: str, moments: list[str]) -> tuple[str, int, int]:
        k, n, _ = ghosts(rows, knows, moments)
        out.append(count(R1, "pooled (findings text)", label, "+".join(moments), k, n))
        return label, k, n

    pooled("float32 precision", "float32 precision", MOMENTS)
    missed = "one in-flight spike missed"
    walk_missed = pooled("missed spike, walking", missed, ["walking"])
    decide_missed = pooled("missed spike, at decisions", missed, ["laced food", "shadow"])
    _, _, missed_fail = ghosts(rows, missed, ["laced food", "shadow"])
    out.append(median(R1, "time to fail", "missed spike, at decisions", "laced food+shadow",
                      missed_fail, "ms"))  # fmt: skip

    claims = [
        ("Finding 1: a missed spike matters at decisions, not while walking",
         walk_missed, decide_missed),
        ("Finding 2: 0.001 mV is not enough at the laced food (vs walking)",
         ("walking", *ghosts(rows, "voltage known to 0.001 mV", ["walking"])[:2]),
         ("laced food", *ghosts(rows, "voltage known to 0.001 mV", ["laced food"])[:2])),
        ("Finding 2: 0.001 mV is not enough at the laced food (vs shadow)",
         ("shadow", *ghosts(rows, "voltage known to 0.001 mV", ["shadow"])[:2]),
         ("laced food", *ghosts(rows, "voltage known to 0.001 mV", ["laced food"])[:2])),
        ("Finding 4: 0.01 mV harmless while walking, fatal at the laced food",
         ("walking", *ghosts(rows, "voltage known to 0.01 mV", ["walking"])[:2]),
         ("laced food", *ghosts(rows, "voltage known to 0.01 mV", ["laced food"])[:2])),
        ("Finding 5: 99.9% observed is not quite enough at the laced food (vs walking)",
         ("walking", *ghosts(rows, "99.9% of neurons observed", ["walking"])[:2]),
         ("laced food", *ghosts(rows, "99.9% of neurons observed", ["laced food"])[:2])),
        ("Finding 5: 99.9% observed is not quite enough at the laced food (vs shadow)",
         ("shadow", *ghosts(rows, "99.9% of neurons observed", ["shadow"])[:2]),
         ("laced food", *ghosts(rows, "99.9% of neurons observed", ["laced food"])[:2])),
    ]  # fmt: skip
    for claim, a, b in claims:
        out.append(difference(R1, claim, a, b))
    return out


# --- Result 2 (ADR-0039) -------------------------------------------------------------

R2 = "2 (ADR-0039)"
# Finding 4's columns: (column, test row, behaviour present?), as in plot_null_brain.py.
SWEEP: list[tuple[str, str, Callable[[Row], bool], str]] = [
    ("walks", "arena 10 s", lambda r: float(r["walked_mm"]) > 10, "walked_mm"),
    ("feeds on food", "food", lambda r: int(r["feeding_ms"]) > 0, "MN9_hz"),
    ("refuses laced food", "laced food", lambda r: int(r["feeding_ms"]) == 0, "MN9_hz"),
    ("escapes", "shadow", lambda r: int(r["jumps"]) > 0, "GF_hz"),
    ("stays quiet", "arena 10 s", lambda r: int(r["neurons_active"]) < 3000, "neurons_active"),
]  # fmt: skip
UNITS = {"walked_mm": "mm walked", "MN9_hz": "MN9 Hz", "GF_hz": "GF Hz",
         "neurons_active": "neurons active"}  # fmt: skip
# Finding 1, held in place: (probe, readout, behaviour present?).
PROBES: list[tuple[str, str, Callable[[Row], bool]]] = [
    ("walking ground", "walks (P9)", lambda r: float(r["P9_hz"]) > 0),
    ("food", "feeds (MN9)", lambda r: int(r["feeding_ms"]) > 0),
    ("bitter", "refuses (MN9)", lambda r: int(r["feeding_ms"]) == 0),
    ("laced food", "refuses (MN9)", lambda r: int(r["feeding_ms"]) == 0),
    ("shadow", "jumps (GF)", lambda r: int(r["jumps"]) > 0),
]  # fmt: skip


def share_label(share: float) -> str:
    return "0% (real)" if share == 0 else f"{share:.0%}"


def tally(rows: list[Row], test: str, present: Callable[[Row], bool]) -> tuple[int, int]:
    mine = [r for r in rows if r["test"] == test]
    return sum(present(r) for r in mine), len(mine)


def result_2(full: list[Row], sweep: list[Row], free: list[Row]) -> list[Out]:
    out: list[Out] = []
    real = [r for r in full if r["brain"] == "real"]
    null = [r for r in full if r["brain"].startswith("null")]

    # Finding 1: arena and probes, real (3 seeds) against full null brains (5 x 3 seeds).
    arena: list[tuple[str, Callable[[Row], bool]]] = [
        ("moves (walked > 0 mm)", lambda r: float(r["walked_mm"]) > 0),
        ("reaches the food", lambda r: r["reached_food"] == "True"),
        ("feeds", lambda r: int(r["feeding_ms"]) > 0),
        ("escapes the shadow", lambda r: r["escaped_shadow"] == "True"),
    ]  # fmt: skip
    table = "finding 1 (real vs full null)"
    for column, present in arena:
        for name, brains in (("real", real), ("full null", null)):
            out.append(count(R2, table, f"arena: {column}", name, *tally(brains, "arena 10 s",
                                                                         present)))  # fmt: skip
    for probe, column, present in PROBES:
        for name, brains in (("real", real), ("full null", null)):
            out.append(count(R2, table, f"held in place, {probe}: {column}", name,
                             *tally(brains, probe, present)))  # fmt: skip
    arena_real = [r for r in real if r["test"] == "arena 10 s"]
    for column, unit in (("walked_mm", "mm"), ("feeding_ms", "ms")):
        values = [float(r[column]) for r in arena_real]
        out.append(median(R2, table, f"arena: {column}", "real", values, unit))
    for probe, readout in (("walking ground", "P9_hz"), ("food", "MN9_hz"), ("shadow", "GF_hz")):
        values = [float(r[readout]) for r in real if r["test"] == probe]
        out.append(median(R2, table, f"held in place, {probe}: {readout}", "real", values, "Hz"))

    # Finding 4: the sweep table (0% = real rows, 100% = full null rows, as in the ADR).
    rows = full + sweep
    shares = sorted({float(r["rewired"]) for r in rows})
    table = "finding 4 (partial rewiring)"
    counts: dict[tuple[str, float], tuple[int, int]] = {}
    for share in shares:
        mine = [r for r in rows if float(r["rewired"]) == share]
        for column, test, present, value in SWEEP:
            k, n = tally(mine, test, present)
            counts[column, share] = (k, n)
            out.append(count(R2, table, share_label(share), column, k, n))
            values = [float(r[value]) for r in mine if r["test"] == test]
            out.append(median(R2, "sweep figure medians", share_label(share),
                              f"{column}: {value}", values, UNITS[value]))  # fmt: skip

    # Pooled over 5-25%, the range where finding 4 says the decision has broken but the
    # single-sense behaviours have not: one share alone (n = 3) cannot separate them.
    early = [s for s in shares if 0.05 <= s <= 0.25]
    pooled: dict[str, tuple[str, int, int]] = {}
    for column, *_ in SWEEP:
        k = sum(counts[column, s][0] for s in early)
        n = sum(counts[column, s][1] for s in early)
        pooled[column] = (f"{column}, 5-25%", k, n)
        out.append(count(R2, "pooled (findings text)", "5-25% rewired", column, k, n))
    single_k = sum(pooled[c][1] for c in ("walks", "feeds on food", "escapes"))
    single_n = sum(pooled[c][2] for c in ("walks", "feeds on food", "escapes"))
    out.append(count(R2, "pooled (findings text)", "5-25% rewired",
                     "walks, feeds or escapes (each one sense)", single_k, single_n))  # fmt: skip

    def at(column: str, share: float) -> tuple[str, int, int]:
        return (f"{column}, {share_label(share)}", *counts[column, share])

    claims: list[tuple[str, tuple[str, int, int], tuple[str, int, int]]] = [
        ("Finding 1: real brains walk, full null brains never move",
         at("walks", 0.0), at("walks", 1.0)),
        ("Finding 1: real brains feed on food, full null brains do not",
         at("feeds on food", 0.0), at("feeds on food", 1.0)),
        ("Finding 1: real brains escape, full null brains do not",
         at("escapes", 0.0), at("escapes", 1.0)),
        ("Finding 4: refusing laced food breaks at 5%",
         at("refuses laced food", 0.0), at("refuses laced food", 0.05)),
        ("Finding 4: refusing laced food breaks at 10%",
         at("refuses laced food", 0.0), at("refuses laced food", 0.1)),
        ("Finding 4: refusing laced food breaks at 25%",
         at("refuses laced food", 0.0), at("refuses laced food", 0.25)),
        ("Finding 4: refusing laced food breaks at 5-25% (pooled)",
         at("refuses laced food", 0.0), pooled["refuses laced food"]),
        ("Finding 4: the decision breaks first (single-sense vs refusing, 5-25%)",
         ("walks/feeds/escapes, 5-25%", single_k, single_n), pooled["refuses laced food"]),
        ("Finding 4: runaway activity between 5% and 50% (stays quiet, real vs 50%)",
         at("stays quiet", 0.0), at("stays quiet", 0.5)),
        ("Finding 4: feeding is gone by 75% (real vs 75%)",
         at("feeds on food", 0.0), at("feeds on food", 0.75)),
    ]  # fmt: skip
    # "Survives" claims are not tested as differences: no detectable difference from the
    # real brain at n = 3 is not evidence of survival. They rest on the counts above.
    for claim, a, b in claims:
        out.append(difference(R2, claim, a, b))

    # Finding 3, decoder-free: the situation read from deep neurons (held-out seed).
    table = "finding 3 (decoder-free)"
    reads = [r for r in free if r["read_trials"]]
    groups: dict[str, list[Row]] = {}
    for r in reads:
        group = "real" if r["brain"] == "real" else f"{float(r['rewired']):.0%} rewired"
        if group == "100% rewired":
            group = "full null (5)"
        groups.setdefault(group, []).append(r)
    for group, mine in groups.items():
        for r in mine:
            out.append(count(R2, table, "situation read right", f"{group}: {r['brain']}",
                             int(r["read_right"]), int(r["read_trials"])))  # fmt: skip
        k = sum(int(r["read_right"]) for r in mine)
        n = sum(int(r["read_trials"]) for r in mine)
        out.append(count(R2, table, "situation read right (pooled)", group, k, n))
    return out


def main() -> None:
    horizon = list(csv.DictReader((ASSETS / "horizon_v2.csv").open()))
    full = list(csv.DictReader((ASSETS / "null_brain.csv").open()))
    sweep = list(csv.DictReader((ASSETS / "null_brain_sweep.csv").open()))
    free = list(csv.DictReader((ASSETS / "decoder_free.csv").open()))

    walking_missed = ghosts(horizon, "one in-flight spike missed", ["walking"])[1]
    if walking_missed != 6:  # ADR-0038 correction: seed 0's three void runs are removed
        raise SystemExit(f"walking missed-spike ghosts: {walking_missed}, expected 6")

    out = result_1(horizon) + result_2(full, sweep, free)
    path = ASSETS / "uncertainty_results_1_2.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out)
    for entry in out:
        print(f"{entry['result']} | {entry['table']} | {entry['row']} | {entry['column']} | "
              f"{entry['shown_as']}")  # fmt: skip
    print(f"wrote {path.name}: {len(out)} rows")


if __name__ == "__main__":
    main()
