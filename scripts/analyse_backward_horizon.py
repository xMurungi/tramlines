"""Result 4's analysis, exactly as pre-registered (docs/science/backward-horizon-plan.md).

Reads docs/assets/backward_horizon.csv and exact_check.csv; judges H1-H5 by their
stated criteria; writes docs/assets/backward_horizon_summary.csv and the figures
backward_horizon.png and exact_check.png.

    uv run python scripts/analyse_backward_horizon.py
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
SURFACE, INK, MUTED, GRID = "#07070a", "#e9e3d6", "#8a8478", "#24222a"
BACKWARD, FORWARD = "#bb861f", "#6f93d6"  # validated pair (ADR-0039): ΔE 23.6
MOMENTS = ["walking", "laced food", "shadow"]
DECISIONS = {"laced food", "shadow"}
HORIZON_MS = 3_000
Row = dict[str, str]


def wilson(k: int, n: int) -> str:
    """k/n with its Wilson 95% interval."""
    if n == 0:
        return "0/0"
    z, p = 1.959964, k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return f"{k}/{n} [{max(0, centre - half):.0%}-{min(1, centre + half):.0%}]"


def interval(k: int, n: int) -> tuple[float, float]:
    z, p = 1.959964, k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def median_ci(values: list[int]) -> str:
    """Median of uncensored B with a bootstrap 95% interval (10,000 resamples, seed 0)."""
    if not values:
        return "-"
    rng = np.random.default_rng(0)
    data = np.array(values)
    boots = np.median(rng.choice(data, (10_000, len(data))), axis=1)
    low, high = np.percentile(boots, [2.5, 97.5])
    return f"{np.median(data):.0f} ms [{low:.0f}-{high:.0f}]"


def b(row: Row, eps: str, which: str = "brain") -> int | None:
    value = row[f"B_{which}_{eps}"]
    return int(value) if value else None


def judge(rows: list[Row], exact: list[Row]) -> list[tuple[str, str, str]]:
    made = [r for r in rows if r["made"] == "True"]
    voltage = [r for r in made if r["kind"] == "voltage"]
    small = [r for r in voltage if float(r["amount_mV"]) <= 1e-3]
    spikes = [r for r in made if r["kind"] != "voltage" and r["moment"] in DECISIONS]
    out = []

    k1 = sum(b(r, "1e-13") is None for r in voltage)
    k2 = sum((v := b(r, "1e-09")) is not None and v <= 1_000 for r in small)
    ok = k1 >= 0.9 * len(voltage) and k2 >= 0.9 * len(small)
    out.append(("H1 rounding floor", "supported" if ok else "not supported",
                f"B(1e-13) censored {wilson(k1, len(voltage))}; "
                f"B(1e-9) <= 1 s for sigma <= 1e-3: {wilson(k2, len(small))}"))  # fmt: skip

    k = sum(b(r, "1e-09") is not None for r in spikes)
    out.append(("H2 brain forgets spikes", "supported" if k >= 0.5 * len(spikes) else
                "not supported", f"B(1e-9) <= 3 s: {wilson(k, len(spikes))}"))  # fmt: skip

    ks = sum(r["body_differs"] == "True" for r in spikes)
    kv = sum(r["body_differs"] == "True" for r in small)
    ok = ks >= 0.5 * len(spikes) and kv <= 0.25 * len(small)
    out.append(("H3 body remembers", "supported" if ok else "not supported",
                f"spike pairs at decisions: body differs {wilson(ks, len(spikes))}; "
                f"voltage <= 1e-3: {wilson(kv, len(small))}"))  # fmt: skip

    body = [r for r in made if r["body_differs"] == "True"]
    still = [r for r in made if r["body_differs"] != "True"]
    kb = sum(b(r, "1e-09") is None for r in body)
    kn = sum(b(r, "1e-09") is None for r in still)
    if body and still:
        (lb, _), (_, hn) = interval(kb, len(body)), interval(kn, len(still))
        verdict = ("supported" if lb > hn else "suggestive" if kb / len(body) > kn / len(still)
                   else "not supported")  # fmt: skip
    else:
        verdict = "not testable"
    out.append(("H4 body keeps brain apart", verdict,
                f"brain still distinguishable at 3 s (1e-9): body differs {wilson(kb, len(body))}, "
                f"body same {wilson(kn, len(still))}"))  # fmt: skip

    f64 = [float(r["max_dv_mV_float64"]) for r in exact]
    exact50 = [float(r["max_dv_mV_50_digits"]) for r in exact]
    floor_above = min(f64) > 1e-14
    ok = floor_above and min(exact50) < 1e-20
    out.append(("H5 floor is the computer's", "supported" if ok else "not supported",
                f"test network float64 smallest {min(f64):.1e} mV (criterion: stays above 1e-14); "
                f"50 digits smallest {min(exact50):.1e} mV (criterion: below 1e-20)"))  # fmt: skip
    return out


def table(rows: list[Row]) -> list[dict[str, str]]:
    out = []
    kinds = [("voltage", "1e-09"), ("voltage", "1e-06"), ("voltage", "0.001"), ("voltage", "0.1"),
             ("missed spike", ""), ("extra spike", "")]  # fmt: skip
    for moment in MOMENTS:
        for kind, amount in kinds:
            mine = [r for r in rows if r["moment"] == moment and r["kind"] == kind
                    and (not amount or float(r["amount_mV"]) == float(amount))]  # fmt: skip
            made = [r for r in mine if r["made"] == "True"]
            entry = {"moment": moment,
                     "difference": f"voltage {amount} mV" if amount else kind,
                     "made": f"{len(made)}/{len(mine)}"}  # fmt: skip
            for eps in ("1e-11", "1e-09", "1e-06"):
                values = [v for r in made if (v := b(r, eps)) is not None]
                entry[f"B_brain({eps})"] = (f"{median_ci(values)}; "
                                            f"> 3 s: {len(made) - len(values)}")  # fmt: skip
            entry["body differs"] = wilson(
                sum(r["body_differs"] == "True" for r in made), len(made)
            )
            out.append(entry)
    return out


def plot(rows: list[Row], exact: list[Row]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    forward = list(csv.DictReader((ASSETS / "horizon_v2.csv").open()))
    forward_label = {"voltage 0.001 mV": "voltage known to 0.001 mV",
                     "voltage 0.1 mV": "voltage known to 0.1 mV",
                     "missed spike": "one in-flight spike missed"}  # fmt: skip
    kinds: list[tuple[str, str, float | None]] = [
        ("voltage 1e-09 mV", "voltage", 1e-9),
        ("voltage 1e-06 mV", "voltage", 1e-6),
        ("voltage 0.001 mV", "voltage", 1e-3),
        ("voltage 0.1 mV", "voltage", 0.1),
        ("missed spike", "missed spike", None),
        ("extra spike", "extra spike", None),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.8), dpi=160, sharey=True, facecolor=SURFACE)
    censored_x = 3.35
    for ax, moment in zip(axes, MOMENTS, strict=True):
        ax.set_facecolor(SURFACE)
        for i, (label, kind, amount) in enumerate(kinds):
            mine = [r for r in rows if r["moment"] == moment and r["kind"] == kind
                    and r["made"] == "True"
                    and (amount is None or float(r["amount_mV"]) == amount)]  # fmt: skip
            for j, r in enumerate(mine):
                v = b(r, "1e-09")
                x = censored_x if v is None else v / 1000
                filled = r["body_differs"] == "True"
                ax.scatter([x], [i - 0.15 + 0.3 * j / max(1, len(mine) - 1)], s=18,
                           facecolors=BACKWARD if filled else "none", edgecolors=BACKWARD,
                           linewidths=1)  # fmt: skip
            if label in forward_label:
                wanted = forward_label[label]
                fw = [int(r["path_stays_right_ms"]) / 1000 for r in forward
                      if r["moment"] == moment and r["ghost_knows"] == wanted]  # fmt: skip
                ax.scatter([min(x, 3.0) for x in fw], [i + 0.3] * len(fw), s=10, color=FORWARD,
                           marker="D", linewidths=0, alpha=0.8)  # fmt: skip
        ax.axvline(3.15, color=GRID, linewidth=1)
        ax.set_xlim(-0.05, 3.6)
        ax.set_xticks([0, 1, 2, 3, censored_x])
        ax.set_xticklabels(["0", "1", "2", "3", "> 3"])
        ax.set_title(moment, color=INK, fontsize=10, loc="left")
        ax.set_xlabel("seconds", color=MUTED, fontsize=8)
        ax.tick_params(colors=MUTED, labelsize=8)
        ax.grid(axis="x", color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)
    axes[0].set_yticks(range(len(kinds)))
    axes[0].set_yticklabels([k[0] for k in kinds], color=INK, fontsize=8)
    axes[0].invert_yaxis()
    handles = [
        Line2D([], [], marker="o", linestyle="", color=BACKWARD,
               label="backward: brain no longer shows the past (to 1e-9 mV)"),
        Line2D([], [], marker="o", linestyle="", markerfacecolor="none", color=BACKWARD,
               label="hollow: the body forgot too; filled: the body still shows it"),
        Line2D([], [], marker="D", linestyle="", color=FORWARD,
               label="forward (Result 1): ghost's path stays right"),
    ]  # fmt: skip
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, labelcolor=INK,
               fontsize=7)  # fmt: skip
    fig.suptitle("The backward horizon: how long the present still shows a small difference in"
                 " the past (3 seeds)", color=INK, fontsize=10, x=0.01, ha="left")  # fmt: skip
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    fig.savefig(ASSETS / "backward_horizon.png", facecolor=SURFACE)

    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=160, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    t = [int(r["time_ms"]) for r in exact]
    series = [
        ("max_dv_mV_float64", "busy network, float64", BACKWARD, "-"),
        ("max_dv_mV_50_digits", "busy network, 50 digits", FORWARD, "-"),
        ("quiet_neuron_from_rest_mV_float64", "one quiet neuron, float64", BACKWARD, "--"),
        ("quiet_neuron_from_rest_mV_50_digits", "one quiet neuron, 50 digits", FORWARD, "--"),
    ]
    for column, label, color, style in series:
        values = [max(float(r[column]), 1e-33) for r in exact]  # zero drawn at the bottom
        ax.plot(t, values, color=color, linestyle=style, linewidth=2, label=label)
    ax.set_yscale("log")
    ax.set_ylim(1e-33, 1e-8)
    ax.set_xlabel("ms after the 1e-9 mV difference", color=MUTED, fontsize=8)
    ax.set_ylabel("difference (mV); exactly 0 drawn at the bottom", color=MUTED, fontsize=8)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(color=GRID, linewidth=0.6)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(frameon=False, labelcolor=INK, fontsize=7)
    ax.set_title("Rounding decides: float64 erases (busy) or freezes (quiet); exact arithmetic"
                 " only fades", color=INK, fontsize=9, loc="left")  # fmt: skip
    fig.tight_layout()
    fig.savefig(ASSETS / "exact_check.png", facecolor=SURFACE)


def main() -> None:
    rows = list(csv.DictReader((ASSETS / "backward_horizon.csv").open()))
    exact = list(csv.DictReader((ASSETS / "exact_check.csv").open()))
    made = [r for r in rows if r["made"] == "True"]
    print(f"pairs: {len(rows)}, made {len(made)}; not made: "
          f"{sorted({r['why_not'] for r in rows if r['made'] != 'True'})}")  # fmt: skip
    for subset, label in (
        (rows, "all seeds"),
        ([r for r in rows if r["seed"] != "0"], "seeds 1-2"),
    ):
        print(f"== hypotheses, {label}")
        for name, verdict, evidence in judge(subset, exact):
            print(f"  {name}: {verdict.upper()} | {evidence}")
    summary = table(rows)
    out = ASSETS / "backward_horizon_summary.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    for entry in summary:
        print(" | ".join(entry.values()))
    plot(rows, exact)
    print(f"wrote {out.name}, backward_horizon.png, exact_check.png")


if __name__ == "__main__":
    main()
