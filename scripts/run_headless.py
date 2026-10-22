"""Run the whole fly (brain + senses + body + world) without a viewer, and plot its path.

    uv run python scripts/run_headless.py                # 10 s, seed 0, default arena
    uv run python scripts/run_headless.py --seconds 4 --seed 3 --tag short

Writes docs/assets/headless_<tag>.png and a one-line-per-event summary to stdout.
This is the Phase 3 gate run (CLAUDE.md 10).
"""

from __future__ import annotations

import argparse
import math
import time
from pathlib import Path

from tramlines.brain.connectome import load_connectome
from tramlines.brain.engine import enable_determinism
from tramlines.brain.neurons import load_catalog
from tramlines.timeline.timeline import Pose, Timeline
from tramlines.world.arena import DEFAULT_ARENA, Arena
from tramlines.world.decoder import FlyDecoder
from tramlines.world.fly import FlyState
from tramlines.world.senses import FlySenses

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
START = FlyState(x_mm=-2.0, y_mm=14.0, heading_rad=0.0)  # presentation choice (ADR-0028)


def events(poses: list[Pose], arena: Arena) -> list[str]:
    out, feeding, on = [], False, frozenset[str]()
    for p in poses:
        here = frozenset(patch.kind for patch in arena.patches_under(p.x_mm, p.y_mm))
        for kind in sorted(here - on):
            out.append(f"{p.time_ms / 1000:6.3f} s  steps onto {kind}")
        for kind in sorted(on - here):
            out.append(f"{p.time_ms / 1000:6.3f} s  leaves {kind}")
        if p.feeding != feeding:
            out.append(f"{p.time_ms / 1000:6.3f} s  {'starts' if p.feeding else 'stops'} feeding")
        if p.jumped:
            out.append(f"{p.time_ms / 1000:6.3f} s  jumps")
        feeding, on = p.feeding, here
    return out


def plot(poses: list[Pose], arena: Arena, out: Path, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    surface, ink, muted, gold = "#07070a", "#e9e3d6", "#8a8478", "#bb861f"
    fig, ax = plt.subplots(figsize=(6.4, 6.4), dpi=160, facecolor=surface)
    ax.set_facecolor(surface)
    ax.add_patch(Circle((0, 0), arena.radius_mm, fill=False, color=muted, linewidth=1))
    for patch in arena.patches:
        style = {"food": "-", "bitter": "--"}[patch.kind]
        ax.add_patch(
            Circle((patch.x_mm, patch.y_mm), patch.radius_mm, fill=False, color=ink, ls=style)
        )
        ax.annotate(patch.kind, (patch.x_mm, patch.y_mm + patch.radius_mm + 1), color=ink,
                    ha="center", fontsize=8)  # fmt: skip
    for loom in arena.looms:
        x, y = (
            0.92 * arena.radius_mm * math.cos(loom.direction_rad),
            0.92 * arena.radius_mm * math.sin(loom.direction_rad),
        )
        ax.annotate(f"shadow at {loom.start_ms / 1000:g} s", (x, y), color=muted, ha="center",
                    fontsize=8)  # fmt: skip
    xs, ys = [p.x_mm for p in poses], [p.y_mm for p in poses]
    ax.plot(xs, ys, color=gold, linewidth=1.6)
    ax.plot(xs[0], ys[0], "o", color=gold, markersize=6)
    ax.annotate("start", (xs[0], ys[0] - 2.5), color=ink, ha="center", fontsize=8)
    feed = [p for p in poses if p.feeding]
    if feed:
        ax.plot([p.x_mm for p in feed], [p.y_mm for p in feed], "s", color=ink, markersize=5)
        ax.annotate("feeds", (feed[0].x_mm + 1.5, feed[0].y_mm), color=ink, fontsize=8)
    for p in poses:
        if p.jumped:
            ax.plot(p.x_mm, p.y_mm, "^", color=ink, markersize=8)
            ax.annotate("jump", (p.x_mm + 1.5, p.y_mm), color=ink, fontsize=8)
    ax.set_xlim(-arena.radius_mm - 2, arena.radius_mm + 2)
    ax.set_ylim(-arena.radius_mm - 2, arena.radius_mm + 2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, color=ink, fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(out, facecolor=surface)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--tag", default="seed0")
    args = parser.parse_args()

    enable_determinism()
    catalog = load_catalog()
    timeline = Timeline(
        load_connectome(),
        DEFAULT_ARENA,
        FlySenses.from_catalog(catalog),
        FlyDecoder.from_catalog(catalog),
        seed=args.seed,
        start=START,
    )
    start = time.perf_counter()
    poses = timeline.run(round(args.seconds * 1000))
    wall = time.perf_counter() - start
    for line in events(poses, DEFAULT_ARENA):
        print(line)
    print(f"simulated {args.seconds:g} s in {wall:.1f} s ({args.seconds / wall:.2f}x real time)")
    print(f"fingerprint {timeline.fingerprint()[:16]}")
    ASSETS.mkdir(parents=True, exist_ok=True)
    title = f"Headless run: seed {args.seed}, {args.seconds:g} s (the path is the brain's)"
    plot(poses, DEFAULT_ARENA, ASSETS / f"headless_{args.tag}.png", title)


if __name__ == "__main__":
    main()
