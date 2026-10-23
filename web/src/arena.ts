// The arena seen from above: the dish, food and bitter, a looming shadow, the fly and its ghost.

import type { Ghost, PoseRow, Run } from "./model";

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

  draw(run: Run, playhead: number): void {
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

    // The ghost: the independent prediction, drawn ahead of the fly.
    const ghost = run.ghostFor(playhead);
    if (ghost) this.drawGhost(ghost, playhead, toX, toY);

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

  private drawGhost(ghost: Ghost, playhead: number, toX: (x: number) => number, toY: (y: number) => number): void {
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
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) ctx.filter = "blur(1.5px)";
    this.drawFly(ahead[ahead.length - 1], toX, toY, css("--ghost-fly"), 1);
    ctx.restore();
  }

  private drawFly(p: PoseRow, toX: (x: number) => number, toY: (y: number) => number, color: string, alpha: number): void {
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
