"""Figure for Result 3 (ADR-0048), the planned atlas.png (docs/science/atlas-plan.md).

uv run python scripts/plot_atlas.py   # reads docs/assets/atlas_{screen,outcomes,decoder}.csv
"""

from __future__ import annotations

from pathlib import Path

from analyse_atlas import GROUPS, MOMENTS, change_rate, is_true, load, wilson

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
SURFACE, INK, MUTED, GRID = "#07070a", "#e9e3d6", "#8a8478", "#24222a"
COLOURS = {"random": "#bb861f", "awake": "#6f93d6", "inputs": "#c2667e"}  # validated, dark
NAMES = {"random": "random neurons", "awake": "active neurons", "inputs": "sensory inputs"}


def main() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    screen, follow, rerun = load("screen"), load("outcomes"), load("decoder")
    made = [r for r in screen if r["made"] == "True"]
    seeds = sorted({r["seed"] for r in screen})
    secs = [m / 1000 for m in MOMENTS]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), dpi=160, facecolor=SURFACE,
                             gridspec_kw={"width_ratios": [1.2, 1.2, 0.8]})  # fmt: skip
    for ax in axes:
        ax.set_facecolor(SURFACE)
        ax.tick_params(colors=MUTED, labelsize=8)
        ax.grid(color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)

    # 1. Cascade rate per moment and group (E1).
    ax = axes[0]
    for g in GROUPS:
        ys, los, his = [], [], []
        for m in MOMENTS:
            rows = [r for r in made if r["group"] == g and int(r["moment_ms"]) == m]
            k = sum(int(r["spike_differences"]) > 0 for r in rows)
            lo, hi = wilson(k, len(rows))
            ys.append(100 * k / len(rows))
            los.append(100 * lo)
            his.append(100 * hi)
        ax.fill_between(secs, los, his, color=COLOURS[g], alpha=0.18, linewidth=0)
        ax.plot(secs, ys, color=COLOURS[g], linewidth=2)
        ax.annotate(NAMES[g], (secs[-1], ys[-1]), xytext=(4, 0), textcoords="offset points",
                    va="center", color=INK, fontsize=7)  # fmt: skip
    ax.set_xlim(0, 4.6)
    ax.set_ylim(0, 85)
    ax.set_xlabel("moment (s); laced food ~1.2 s, shadow 3.0-3.5 s", color=MUTED, fontsize=8)
    ax.set_ylabel("% of extra spikes that change other spikes (30 ms)", color=MUTED, fontsize=8)
    ax.set_title("1 · Does one extra spike ripple?", color=INK, fontsize=10, loc="left")

    # 2. Choice-change rate for a random spike per moment (E2).
    ax = axes[1]
    rnd_s = [r for r in screen if r["group"] == "random"]
    rnd_f = [r for r in follow if r["group"] == "random"]
    rates = [100 * change_rate(rnd_s, rnd_f, {(s, str(m)) for s in seeds}) for m in MOMENTS]
    ax.bar(secs, rates, width=0.32, color=COLOURS["random"])
    for x, v in zip(secs, rates, strict=True):
        ax.annotate(f"{v:.1f}%", (x, v), xytext=(0, 3), textcoords="offset points", ha="center",
                    color=INK, fontsize=7)  # fmt: skip
    ax.set_xlabel("moment (s)", color=MUTED, fontsize=8)
    ax.set_ylabel("% of random extra spikes that change the fly's choice", color=MUTED, fontsize=8)
    ax.set_ylim(0, max(rates) * 1.25)
    ax.set_title("2 · Does it change what the fly does?", color=INK, fontsize=10, loc="left")

    # 3. Tipping points under other decoders (E4).
    ax = axes[2]
    variants = ["thresholds x0.8", "thresholds x1.2", "window 100 ms"]
    vals, labels = [], []
    for variant in variants:
        tip = [r for r in rerun if r["variant"] == variant and is_true(r, "tipping_by_default")
               and r["made"] == "True"]  # fmt: skip
        k = sum(is_true(r, "choice_differs") for r in tip)
        vals.append(100 * k / len(tip))
        labels.append(f"{k}/{len(tip)}")
    ax.barh(range(3), vals, color=COLOURS["awake"], height=0.55)
    for i, (v, lab) in enumerate(zip(vals, labels, strict=True)):
        ax.annotate(f"{v:.0f}% ({lab})", (v, i), xytext=(4, 0), textcoords="offset points",
                    va="center", color=INK, fontsize=7)  # fmt: skip
    ax.axvline(70, color=MUTED, linewidth=1, linestyle="--")
    ax.set_yticks(range(3))
    ax.set_yticklabels(["thresholds -20%", "thresholds +20%", "slower readout\n(100 ms)"],
                       color=INK, fontsize=8)  # fmt: skip
    ax.invert_yaxis()
    ax.set_xlim(0, 130)
    ax.set_xlabel("% that still tip (dashed: 70% criterion)", color=MUTED,
                  fontsize=8)  # fmt: skip
    ax.set_title("3 · Is it the brain, or our decoder?", color=INK, fontsize=10, loc="left")

    fig.suptitle("Result 3 · 61,848 single extra spikes in a 138,639-neuron fly brain (3 seeds)",
                 color=INK, fontsize=10, x=0.01, ha="left")  # fmt: skip
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(ASSETS / "atlas.png", facecolor=SURFACE)


if __name__ == "__main__":
    main()
