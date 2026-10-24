"""Figure for Result 2: the real wiring against null brains (ADR-0039).

uv run python scripts/plot_null_brain.py   # reads docs/assets/null_brain*.csv

Writes null_brain.png (real against full null brains) and null_brain_sweep.png (how
behaviour fails as more of the wiring is rewired).
"""

from __future__ import annotations

import csv
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.axes import Axes

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
SURFACE, INK, MUTED, GRID = "#07070a", "#e9e3d6", "#8a8478", "#24222a"
REAL, NULL = "#bb861f", "#6f93d6"  # validated pair: normal-vision ΔE 23.6, CVD ΔE 23.7
# The readout that carries each probe's behaviour (FlyDecoder).
KEY_READOUT = {
    "walking ground": ("P9", "walks"),
    "food": ("MN9", "feeds"),
    "bitter": ("MN9", "feeds"),
    "laced food": ("MN9", "feeds"),
    "shadow": ("GF", "jumps"),
}


def behaved(row: dict[str, str], verb: str) -> bool:
    if verb == "walks":
        return float(row["P9_hz"]) > 0
    return int(row["feeding_ms" if verb == "feeds" else "jumps"]) > 0


def style(ax: Axes) -> None:
    ax.set_facecolor(SURFACE)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)


def main() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    runs = list(csv.DictReader((ASSETS / "null_brain.csv").open()))
    wiring = list(csv.DictReader((ASSETS / "null_brain_convergence.csv").open()))
    fig, (left, right) = plt.subplots(
        1, 2, figsize=(11, 4.6), dpi=160, facecolor=SURFACE, gridspec_kw={"width_ratios": [1.25, 1]}
    )

    # Left: each pathway's key readout, fly held in place, one dot per brain and seed.
    probes = list(KEY_READOUT)
    for i, probe in enumerate(probes):
        readout, verb = KEY_READOUT[probe]
        for kind, color, offset in (("real", REAL, -0.15), ("null", NULL, 0.15)):
            mine = [r for r in runs if r["test"] == probe and r["brain"].startswith(kind)]
            left.scatter([float(r[f"{readout}_hz"]) for r in mine], [i + offset] * len(mine),
                         s=26, color=color, alpha=0.85, linewidths=0)  # fmt: skip
            did = sum(behaved(r, verb) for r in mine)
            left.annotate(f"{verb} {did}/{len(mine)}", (92, i + offset), va="center",
                          color=INK, fontsize=7)  # fmt: skip
    left.set_yticks(range(len(probes)))
    left.set_yticklabels([f"{p}  ({KEY_READOUT[p][0]})" for p in probes], color=INK, fontsize=8)
    left.invert_yaxis()
    left.set_xlim(-3, 110)
    left.set_xticks([0, 20, 40, 60, 80])
    left.set_xlabel("key readout's firing rate, fly held in place 1 s (Hz)", color=MUTED,
                    fontsize=8)  # fmt: skip
    left.set_title("What each sense drives", color=INK, fontsize=10, loc="left")
    style(left)

    # Right: convergence. Strongest drive any single receiver gets from each sense.
    ports = list(dict.fromkeys(r["port"] for r in wiring))
    for i, port in enumerate(ports):
        for kind, color, offset in (("real", REAL, -0.15), ("null", NULL, 0.15)):
            mine = [r for r in wiring if r["port"] == port and r["brain"].startswith(kind)]
            right.scatter([float(r["strongest_receiver_rise_mV"]) for r in mine],
                          [i + offset] * len(mine), s=26, color=color, alpha=0.85,
                          linewidths=0)  # fmt: skip
    right.axvline(7.0, color=MUTED, linewidth=1, linestyle="--")
    right.text(7.6, 0.99, "threshold (7 mV)", transform=right.get_xaxis_transform(),
               color=MUTED, fontsize=7, va="top")  # fmt: skip
    right.set_xscale("log")
    right.set_xlim(3, 3000)
    right.set_yticks(range(len(ports)))
    right.set_yticklabels(ports, color=INK, fontsize=8)
    right.invert_yaxis()
    right.set_xlabel("mean rise of the most-driven receiver (mV, log scale)", color=MUTED,
                     fontsize=8)  # fmt: skip
    right.set_title("Why: how strongly each sense converges", color=INK, fontsize=10, loc="left")
    style(right)

    handles = [
        Line2D([], [], marker="o", linestyle="", color=REAL, label="real v783 wiring"),
        Line2D([], [], marker="o", linestyle="", color=NULL,
                   label="null brains (degree-preserving shuffles)"),
    ]  # fmt: skip
    fig.legend(handles=handles, loc="upper right", frameon=False, labelcolor=INK, fontsize=8,
               ncol=2)  # fmt: skip
    fig.suptitle("Same neurons, same senses, same decoder: only the wiring differs",
                 color=INK, fontsize=10, x=0.01, ha="left")  # fmt: skip
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(ASSETS / "null_brain.png", facecolor=SURFACE)


# The sweep's panels: (title, test row, value column, behaviour present?, log scale).
Row = dict[str, str]
SWEEP_PANELS: list[tuple[str, str, str, Callable[[Row], bool], bool]] = [
    ("walks (arena)", "arena 10 s", "walked_mm", lambda r: float(r["walked_mm"]) > 10, False),
    ("feeds on food", "food", "MN9_hz", lambda r: int(r["feeding_ms"]) > 0, False),
    ("refuses laced food", "laced food", "MN9_hz", lambda r: int(r["feeding_ms"]) == 0, False),
    ("escapes the shadow", "shadow", "GF_hz", lambda r: int(r["jumps"]) > 0, False),
    ("stays quiet (arena)", "arena 10 s", "neurons_active",
     lambda r: int(r["neurons_active"]) < 3000, True),
]  # fmt: skip
SWEEP_UNITS = {"walked_mm": "mm walked", "MN9_hz": "MN9 (Hz)", "GF_hz": "GF (Hz)",
               "neurons_active": "neurons active"}  # fmt: skip


def plot_sweep() -> None:
    """How behaviour fails as a growing share of the wiring is rewired."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = [r for name in ("null_brain.csv", "null_brain_sweep.csv")
            for r in csv.DictReader((ASSETS / name).open())]  # fmt: skip
    shares = sorted({float(r["rewired"]) for r in rows})
    fig, axes = plt.subplots(1, len(SWEEP_PANELS), figsize=(12, 3.8), dpi=160, facecolor=SURFACE)
    for ax, (title, test, column, present, log) in zip(axes, SWEEP_PANELS, strict=True):
        medians = []
        for i, share in enumerate(shares):
            mine = [r for r in rows if r["test"] == test and float(r["rewired"]) == share]
            values = sorted(float(r[column]) for r in mine)
            color = REAL if share == 0 else NULL
            ax.scatter([i] * len(values), values, s=14, color=color, alpha=0.8, linewidths=0)
            medians.append(values[len(values) // 2])
            did = sum(present(r) for r in mine)
            ax.text(i, 1.0, f"{did}/{len(mine)}", transform=ax.get_xaxis_transform(),
                    ha="center", va="bottom", color=INK, fontsize=6)  # fmt: skip
        ax.plot(range(len(shares)), medians, color=MUTED, linewidth=1, zorder=0)
        if log:
            ax.set_yscale("log")
        ax.set_xticks(range(len(shares)))
        ax.set_xticklabels([f"{s:.0%}" for s in shares], rotation=90)
        ax.set_title(title, color=INK, fontsize=9, loc="left", pad=14)
        ax.set_ylabel(SWEEP_UNITS[column], color=MUTED, fontsize=7)
        style(ax)
        ax.grid(axis="y", color=GRID, linewidth=0.6)
        ax.grid(axis="x", visible=False)
    fig.supxlabel("share of connections rewired (0% = real wiring; degrees kept)", color=MUTED,
                  fontsize=8)  # fmt: skip
    fig.suptitle("How much of the wiring can be scrambled before behaviour fails"
                 " (n/N = brains still doing it)", color=INK, fontsize=10, x=0.01,
                 ha="left")  # fmt: skip
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(ASSETS / "null_brain_sweep.png", facecolor=SURFACE)


if __name__ == "__main__":
    main()
    if (ASSETS / "null_brain_sweep.csv").exists():
        plot_sweep()
