// The arena seen from above: the dish, food and bitter, a looming shadow, the fly and its ghost.

import { CONTROL, type Ghost, type PoseRow, type Run } from "./model";

type Project = (v: number) => number;

function css(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export class ArenaView {
  private ctx: CanvasRenderingContext2D;

  constructor(private canvas: HTMLCanvasElement) {
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("no 2D canvas");
    this.ctx = ctx;
  }

  /** `knowledge` is the setting being watched; `label` names its ghost on the canvas. */
  draw(run: Run, playhead: number, knowledge: string, label: string): void {
    const hello = run.hello;
    if (!hello) return;
    const { canvas, ctx } = this;
    const size = canvas.clientWidth;
    const dpr = window.devicePixelRatio || 1;
    if (canvas.width !== Math.round(size * dpr)) {
      canvas.width = Math.round(size * dpr);
      canvas.height = Math.round(size * dpr);
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, size, size);
    const scale = (size / 2 - 8) / hello.radius_mm;
    const toX = (x: number) => size / 2 + x * scale;
    const toY = (y: number) => size / 2 - y * scale; // arena y points up

    // The dish.
    ctx.strokeStyle = css("--rule");
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, hello.radius_mm * scale, 0, Math.PI * 2);
    ctx.stroke();

    // Food (solid) and bitter (dashed); a laced patch shows both.
    for (const p of hello.patches) {
      ctx.save();
      ctx.strokeStyle = p.kind === "food" ? css("--food") : css("--bitter");
      ctx.globalAlpha = 0.35 + 0.65 * p.strength;
      ctx.setLineDash(p.kind === "food" ? [] : [4, 4]);
      ctx.beginPath();
      ctx.arc(toX(p.x_mm), toY(p.y_mm), p.radius_mm * scale, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }

    // A looming shadow: a dark wedge from its direction, growing as it arrives.
    for (const loom of hello.looms) {
      const progress = (playhead - loom.start_ms) / loom.duration_ms;
      if (progress < 0 || progress > 1) continue;
      const r = hello.radius_mm * scale;
      const spread = 0.15 + 0.6 * progress;
      const gradient = ctx.createRadialGradient(
        toX(Math.cos(loom.direction_rad) * hello.radius_mm), toY(Math.sin(loom.direction_rad) * hello.radius_mm), 0,
        toX(Math.cos(loom.direction_rad) * hello.radius_mm), toY(Math.sin(loom.direction_rad) * hello.radius_mm), r * spread,
      );
      gradient.addColorStop(0, css("--shadow"));
      gradient.addColorStop(1, "transparent");
      ctx.fillStyle = gradient;
      ctx.globalAlpha = 0.25 + 0.75 * Math.min(1, loom.strength * 10);
      ctx.fillRect(0, 0, size, size);
      ctx.globalAlpha = 1;
    }

    // The ghost: the independent prediction, drawn ahead of the fly. An imperfect one is
    // also drawn where it says the fly is now, so it can be seen peeling away (ADR-XXXX).
    const ghost = run.refusalFor(playhead, knowledge) ? undefined : run.ghostFor(playhead, knowledge);
    if (ghost && knowledge !== CONTROL) this.drawPeel(run, ghost, playhead, hello.right_within_mm, toX, toY);
    if (ghost) this.drawGhost(ghost, playhead, label, toX, toY);

    // The live fly and its recent trail.
    const now = run.poseAt(playhead);
    if (!now) return;
    ctx.strokeStyle = css("--gold");
    ctx.lineWidth = 1.5;
    ctx.globalAlpha = 0.5;
    ctx.beginPath();
    let started = false;
    for (let t = Math.max(1, Math.floor(playhead) - 3000); t <= playhead; t += 10) {
      const p = run.poses[t];
      if (!p) continue;
      if (!started) ctx.moveTo(toX(p[1]), toY(p[2]));
      else ctx.lineTo(toX(p[1]), toY(p[2]));
      started = true;
    }
    ctx.stroke();
    ctx.globalAlpha = 1;
    this.drawFly(now, toX, toY, css("--gold"), 1);
  }

  /**
   * The imperfect ghost's past, from its checkpoint to now, against the live fly: on the
   * path in ghost gold, off it (further than Result 1's 0.1 mm) in the "off" colour. Only
   * moments already played are compared, so the screen never reveals the live future.
   */
  private drawPeel(run: Run, ghost: Ghost, playhead: number, within: number, toX: Project, toY: Project): void {
    const { ctx } = this;
    const past = ghost.poses.filter((p) => p[0] <= playhead);
    if (!past.length) return;
    const off = (p: PoseRow) => {
      const live = run.poses[p[0]];
      return live !== undefined && Math.hypot(p[1] - live[1], p[2] - live[2]) > within;
    };
    ctx.save();
    ctx.setLineDash([2, 5]);
    ctx.lineWidth = 1.5;
    let peeled: PoseRow | undefined;
    for (let i = 1; i < past.length; i++) {
      const [a, b] = [past[i - 1], past[i]];
      const isOff = off(b);
      if (isOff && !peeled) peeled = b;
      ctx.strokeStyle = isOff ? css("--ghost-off") : css("--ghost");
      ctx.beginPath();
      ctx.moveTo(toX(a[1]), toY(a[2]));
      ctx.lineTo(toX(b[1]), toY(b[2]));
      ctx.stroke();
    }
    if (peeled) {
      // Where it left the fly's path.
      ctx.setLineDash([]);
      ctx.strokeStyle = css("--ghost-off");
      ctx.beginPath();
      ctx.arc(toX(peeled[1]), toY(peeled[2]), 4, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.restore();
    const now = past[past.length - 1];
    ctx.save();
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) ctx.filter = "blur(1px)";
    this.drawFly(now, toX, toY, off(now) ? css("--ghost-off") : css("--ghost-fly"), 1);
    ctx.restore();
  }

  private drawGhost(ghost: Ghost, playhead: number, label: string, toX: Project, toY: Project): void {
    const { ctx } = this;
    const ahead = ghost.poses.filter((p) => p[0] > playhead);
    if (!ahead.length) return;
    ctx.save();
    ctx.strokeStyle = css("--ghost");
    ctx.setLineDash([2, 5]);
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ahead.forEach((p, i) => (i ? ctx.lineTo(toX(p[1]), toY(p[2])) : ctx.moveTo(toX(p[1]), toY(p[2]))));
    ctx.stroke();
    ctx.restore();
    ctx.save();
    const end = ahead[ahead.length - 1];
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) ctx.filter = "blur(1.5px)";
    this.drawFly(end, toX, toY, css("--ghost-fly"), 1);
    ctx.restore();
    // Name the ghost where it ends, so the control is never mistaken for a prediction.
    ctx.save();
    ctx.font = `10px ${css("--font-mono")}`;
    ctx.fillStyle = css("--text-muted");
    ctx.fillText(label, toX(end[1]) + 10, toY(end[2]) - 8);
    ctx.restore();
  }

  private drawFly(p: PoseRow, toX: Project, toY: Project, color: string, alpha: number): void {
    const { ctx } = this;
    const [, x, y, heading, feeding] = p;
    ctx.save();
    ctx.translate(toX(x), toY(y));
    ctx.rotate(-heading);
    ctx.globalAlpha = alpha;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.ellipse(0, 0, 7, 3.5, 0, 0, Math.PI * 2); // body, pointing along the heading
    ctx.fill();
    ctx.beginPath();
    ctx.arc(7, 0, 2.6, 0, Math.PI * 2); // head
    ctx.fill();
    if (feeding) {
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(9, 0);
      ctx.lineTo(13, 0); // the proboscis, extended
      ctx.stroke();
    }
    ctx.restore();
  }
}
