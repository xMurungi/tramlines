// The brain seen from the front: every neuron a faint point, glowing gold when it fires.

import type { Run } from "./model";

const GLOW_DECAY_PER_SECOND = 6; // a neuron's glow fades over about a sixth of a second

export class BrainView {
  private ctx: CanvasRenderingContext2D;
  private backdrop: HTMLCanvasElement | null = null;
  private glow = new Float32Array(0);
  private lastChunk = -1;
  private lastTime = 0;

  constructor(private canvas: HTMLCanvasElement) {
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("no 2D canvas");
    this.ctx = ctx;
  }

  draw(run: Run, playhead: number, colors: { faint: string; gold: string }): number {
    const { canvas, ctx } = this;
    const n = run.neuronXY.length / 2;
    if (!n) return 0;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    const dpr = window.devicePixelRatio || 1;
    if (canvas.width !== Math.round(width * dpr) || !this.backdrop) {
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      this.backdrop = this.paintBackdrop(run, colors.faint);
      this.glow = new Float32Array(n);
    }
    const project = (i: number): [number, number] => {
      const pad = 6 * dpr;
      const x = pad + (run.neuronXY[2 * i] / 65535) * (canvas.width - 2 * pad);
      const y = pad + (run.neuronXY[2 * i + 1] / 65535) * (canvas.height - 2 * pad);
      return [x, y];
    };

    // Fade, then light up the neurons that fired in the current 100 ms.
    const now = performance.now();
    const fade = Math.exp(-GLOW_DECAY_PER_SECOND * Math.max(0, now - this.lastTime) / 1000);
    this.lastTime = now;
    for (let i = 0; i < n; i++) this.glow[i] *= fade;
    const chunk = Math.floor(playhead / 100) * 100;
    const fired = run.firedByChunk.get(chunk);
    if (fired && chunk !== this.lastChunk) {
      for (const i of fired) this.glow[i] = 1;
      this.lastChunk = chunk;
    }

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(this.backdrop, 0, 0);
    ctx.fillStyle = colors.gold;
    for (let i = 0; i < n; i++) {
      const g = this.glow[i];
      if (g < 0.03) continue;
      const [x, y] = project(i);
      ctx.globalAlpha = g;
      ctx.fillRect(x - dpr, y - dpr, 2 * dpr, 2 * dpr);
    }
    ctx.globalAlpha = 1;
    return fired ? fired.length : 0;
  }

  private paintBackdrop(run: Run, faint: string): HTMLCanvasElement {
    const backdrop = document.createElement("canvas");
    backdrop.width = this.canvas.width;
    backdrop.height = this.canvas.height;
    const ctx = backdrop.getContext("2d");
    if (!ctx) return backdrop;
    const dpr = window.devicePixelRatio || 1;
    const pad = 6 * dpr;
    ctx.fillStyle = faint;
    ctx.globalAlpha = 0.18;
    for (let i = 0; i < run.neuronXY.length / 2; i++) {
      const x = pad + (run.neuronXY[2 * i] / 65535) * (backdrop.width - 2 * pad);
      const y = pad + (run.neuronXY[2 * i + 1] / 65535) * (backdrop.height - 2 * pad);
      ctx.fillRect(x, y, dpr, dpr);
    }
    return backdrop;
  }
}
