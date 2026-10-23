"""Figure for Result 1: how long a ghost with imperfect knowledge stays right (ADR-0037).

uv run python scripts/plot_horizon.py      # reads docs/assets/horizon.csv
"""

from __future__ import annotations

import csv
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"


def main() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = list(csv.DictReader((ASSETS / "horizon.csv").open()))
    moments = list(dict.fromkeys(r["moment"] for r in rows))
    labels = list(dict.fromkeys(r["ghost_knows"] for r in rows))
    surface, ink, muted, grid, gold = "#07070a", "#e9e3d6", "#8a8478", "#24222a", "#bb861f"
    fig, axes = plt.subplots(
        1, len(moments), figsize=(11, 5.2), dpi=160, sharey=True, facecolor=surface
    )
    for ax, moment in zip(axes, moments, strict=True):
        ax.set_facecolor(surface)
        mine = {r["ghost_knows"]: r for r in rows if r["moment"] == moment}
        values = [int(mine[label]["path_stays_right_ms"]) / 1000 for label in labels]
        y = range(len(labels))
        ax.barh(list(y), values, color=gold, height=0.6)
        for i, v in zip(y, values, strict=True):
            text = "all 3 s" if v >= 3 else f"{v * 1000:.0f} ms"
            ax.annotate(text, (v, i), xytext=(4, 0), textcoords="offset points", va="center",
                        color=ink, fontsize=7)  # fmt: skip
        ax.set_title(moment, color=ink, fontsize=10, loc="left")
        ax.set_xlim(0, 3.8)
        ax.set_xticks([0, 1, 2, 3])
        ax.set_xlabel("ghost's path stays right (s)", color=muted, fontsize=8)
        ax.tick_params(colors=muted, labelsize=8)
        ax.grid(axis="x", color=grid, linewidth=0.6)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)
    axes[0].set_yticks(list(range(len(labels))))
    axes[0].set_yticklabels(labels, color=ink, fontsize=8)
    axes[0].invert_yaxis()
    fig.suptitle(
        "How long a ghost that knows the brain imperfectly stays right"
        " (seed 0, decision dish, 3 s)",
        color=ink, fontsize=10, x=0.01, ha="left",
    )  # fmt: skip
    fig.tight_layout()
    fig.savefig(ASSETS / "horizon.png", facecolor=surface)


if __name__ == "__main__":
    main()
