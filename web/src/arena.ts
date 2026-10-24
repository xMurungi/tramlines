// The arena seen from above: the dish, food and bitter, a looming shadow, the fly and its ghost,
// and the free-will fan (ADR-XXXX).

import { CONTROL, type Fan, type FanBranch, type Ghost, type PoseRow, type Run } from "./model";

type Project = (v: number) => number;

function css(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/** How long one branch takes to unfold, ms of wall time: slow, nothing bounces (CLAUDE.md 9.4). */
export const UNFOLD_MS = 4000;
/** A branch reaches its own hue this far from the untouched fly; nearer, it is still gold. */
const PRISM_MM = 0.5;

export function reducedMotion(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** Each branch's hue, in fixed order (never cycled): --branch-1 ... --branch-8. */
export function branchColor(index: number): string {
  return css(`--branch-${(index % 8) + 1}`);
}

function rgb(hex: string): [number, number, number] {
  const n = parseInt(hex.replace("#", ""), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

/** Gold at the fork, the branch's own hue once it is PRISM_MM from the untouched future. */
function prism(gold: string, hue: string, distance_mm: number): string {
  const f = Math.min(1, distance_mm / PRISM_MM);
  const [a, b] = [rgb(gold), rgb(hue)];
  const mix = a.map((v, i) => Math.round(v + (b[i] - v) * f));
  return `rgb(${mix.join(" ")})`;
}

/** 0 → 1 over UNFOLD_MS, easing in and out; at once when motion is reduced. */
function unfolded(arrived: number | undefined, now: number): number {
  if (arrived === undefined || reducedMotion()) return 1;
  const x = Math.min(1, Math.max(0, (now - arrived) / UNFOLD_MS));
  return (1 - Math.cos(Math.PI * x)) / 2;
}

export class ArenaView {
  private ctx: CanvasRenderingContext2D;

  constructor(private canvas: HTMLCanvasElement) {
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("no 2D canvas");
    this.ctx = ctx;
  }

  /**
   * `knowledge` is the setting being watched; `label` names its ghost on the canvas.
   * `fanAt` is the free-will fan on screen, if any; `wallMs` is the wall clock, for unfolding.
   */
  draw(run: Run, playhead: number, knowledge: string, label: string, fanAt: number | null, wallMs: number): void {
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
    // also drawn where it says the fly is now, so it can be seen peeling away (ADR-0042).
    const ghost = run.refusalFor(playhead, knowledge) ? undefined : run.ghostFor(playhead, knowledge);
    if (ghost && knowledge !== CONTROL) this.drawPeel(run, ghost, playhead, hello.right_within_mm, toX, toY);
    if (ghost) this.drawGhost(ghost, playhead, label, toX, toY);

    const fan = fanAt === null ? undefined : run.fans.get(fanAt);
    if (fan) this.drawFan(run, fan, run.branches.get(fan.at_ms) ?? [], wallMs, toX, toY);

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

  /**
   * The fan: the untouched future as a thin gold line, and each branch from the fork point
   * turning from gold to its own hue as it leaves the untouched future. Its end is filled if
   * the fly split for good, hollow if it never split or came back; its number sits beside it,
   * so colour never carries identity alone.
   */
  private drawFan(run: Run, fan: Fan, branches: (FanBranch | undefined)[], now: number, toX: Project, toY: Project): void {
    const { ctx } = this;
    const origin = run.poseAt(fan.at_ms);
    if (!origin) return;
    const gold = css("--gold");
    ctx.save();
    ctx.lineCap = "round";
    if (fan.base.length) {
      ctx.strokeStyle = css("--gold-dim");
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(toX(origin[1]), toY(origin[2]));
      for (const p of fan.base) ctx.lineTo(toX(p[1]), toY(p[2]));
      ctx.stroke();
    }
    branches.forEach((branch) => {
      if (!branch || !branch.poses.length) return;
      const shown = Math.max(1, Math.round(unfolded(run.arrived.get(`${fan.at_ms}:${branch.index}`), now) * branch.poses.length));
      const hue = branchColor(branch.index);
      ctx.lineWidth = 1.5;
      let [x0, y0] = [origin[1], origin[2]];
      for (let i = 0; i < shown; i++) {
        const p = branch.poses[i];
        ctx.strokeStyle = prism(gold, hue, branch.distance_mm[i] ?? 0);
        ctx.beginPath();
        ctx.moveTo(toX(x0), toY(y0));
        ctx.lineTo(toX(p[1]), toY(p[2]));
        ctx.stroke();
        [x0, y0] = [p[1], p[2]];
      }
      if (shown < branch.poses.length) return; // still unfolding: no verdict at its end yet
      const forGood = branch.split && !branch.body_rejoined;
      ctx.beginPath();
      ctx.arc(toX(x0), toY(y0), 3.5, 0, Math.PI * 2);
      ctx.strokeStyle = hue;
      ctx.fillStyle = hue;
      if (forGood) ctx.fill();
      else ctx.stroke();
      ctx.font = `10px ${css("--font-mono")}`;
      ctx.fillStyle = css("--text-muted");
      ctx.fillText(String(branch.index + 1), toX(x0) + 6, toY(y0) + 3 + 9 * ((branch.index % 3) - 1));
    });
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
