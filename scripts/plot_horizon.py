"""Figure for Result 1: how long a ghost with imperfect knowledge stays right (ADR-0037).

uv run python scripts/plot_horizon.py           # reads docs/assets/horizon.csv
uv run python scripts/plot_horizon.py --tag v2  # second pass: one dot per run (ADR-0038)
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"


SURFACE, INK, MUTED, GRID, GOLD = "#07070a", "#e9e3d6", "#8a8478", "#24222a", "#bb861f"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="")
    tag = parser.parse_args().tag
    if tag:
        plot_distributions(tag)
    else:
        plot_first_pass()


def plot_distributions(tag: str) -> None:
    """Every ghost as one dot: seeds and draws spread a case into a distribution."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = list(csv.DictReader((ASSETS / f"horizon_{tag}.csv").open()))
    moments = list(dict.fromkeys(r["moment"] for r in rows))
    labels = list(dict.fromkeys(r["ghost_knows"] for r in rows))
    seeds = sorted({r["seed"] for r in rows})
    fig, axes = plt.subplots(
        1, len(moments), figsize=(11, 5.2), dpi=160, sharey=True, facecolor=SURFACE
    )
    for ax, moment in zip(axes, moments, strict=True):
        ax.set_facecolor(SURFACE)
        for i, label in enumerate(labels):
            mine = [r for r in rows if r["moment"] == moment and r["ghost_knows"] == label]
            values = [int(r["path_stays_right_ms"]) / 1000 for r in mine]
            # Spread the dots of one case vertically by seed so overlaps stay visible.
            offsets = [(seeds.index(r["seed"]) - (len(seeds) - 1) / 2) * 0.18 for r in mine]
            ax.scatter(values, [i + o for o in offsets], s=10, color=GOLD, alpha=0.8,
                       linewidths=0)  # fmt: skip
            right = sum(v >= 3 for v in values)
            ax.annotate(f"{right}/{len(values)}", (3.08, i), va="center", color=INK, fontsize=7)
            expected = max(
                sum(r["ghost_knows"] == label for r in rows if r["moment"] == m) for m in moments
            )
            if len(values) < expected:  # some ghosts could not be made (ADR-0038)
                missing = expected - len(values)
                ax.annotate(f"({missing} not made: none in transit)", (1.2, i), va="center",
                            color=MUTED, fontsize=6)  # fmt: skip
        ax.set_title(moment, color=INK, fontsize=10, loc="left")
        ax.set_xlim(-0.05, 3.5)
        ax.set_xticks([0, 1, 2, 3])
        ax.set_xlabel("ghost's path stays right (s)", color=MUTED, fontsize=8)
        ax.tick_params(colors=MUTED, labelsize=8)
        ax.grid(axis="x", color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)
    axes[0].set_yticks(list(range(len(labels))))
    axes[0].set_yticklabels(labels, color=INK, fontsize=8)
    axes[0].invert_yaxis()
    fig.suptitle(
        f"How long an imperfect ghost stays right: {len(seeds)} seeds, one dot per ghost;"
        " n/N = ghosts right for all 3 s",
        color=INK, fontsize=10, x=0.01, ha="left",
    )  # fmt: skip
    fig.tight_layout()
    fig.savefig(ASSETS / f"horizon_{tag}.png", facecolor=SURFACE)


def plot_first_pass() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = list(csv.DictReader((ASSETS / "horizon.csv").open()))
    moments = list(dict.fromkeys(r["moment"] for r in rows))
    labels = list(dict.fromkeys(r["ghost_knows"] for r in rows))
    surface, ink, muted, grid, gold = SURFACE, INK, MUTED, GRID, GOLD
    fig, axes = plt.subplots(
        1, len(moments), figsize=(11, 5.2), dpi=160, sharey=True, facecolor=surface
    )
    for ax, moment in zip(axes, moments, strict=True):
        ax.set_facecolor(surface)
        mine = {r["ghost_knows"]: r for r in rows if r["moment"] == moment}
        # A case can be missing: no spike in transit to miss at that moment (ADR-0038).
        values = [int(mine[label]["path_stays_right_ms"]) / 1000 if label in mine else 0.0
                  for label in labels]  # fmt: skip
        y = range(len(labels))
        ax.barh(list(y), values, color=gold, height=0.6)
        for i, v in zip(y, values, strict=True):
            text = ("n/a: no spike in transit" if labels[i] not in mine
                    else "all 3 s" if v >= 3 else f"{v * 1000:.0f} ms")  # fmt: skip
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
