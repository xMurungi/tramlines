import "./styles/tokens.css";
import "./styles/viewer.css";
import { ArenaView } from "./arena";
import { BrainView } from "./brainView";
import { Run } from "./model";
import { connect } from "./socket";

const run = new Run();
const arena = new ArenaView(document.querySelector<HTMLCanvasElement>("#arena")!);
const brain = new BrainView(document.querySelector<HTMLCanvasElement>("#brain")!);
const $ = (id: string) => document.getElementById(id)!;
const css = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

let connected = false;
let playhead = 0; // ms of simulated time on screen
let playing = false;
let last = performance.now();

connect(
  (message) => run.accept(message),
  (open) => (connected = open),
);
$("replay").addEventListener("click", () => {
  playhead = 0;
  playing = false;
});

function clock(ms: number): string {
  const s = Math.max(0, ms) / 1000;
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${(s % 60).toFixed(3).padStart(6, "0")}`;
}

function frame(now: number): void {
  const dt = Math.min(100, now - last);
  last = now;
  const hello = run.hello;
  const { frontier_ms, computing } = run.status;
  const horizon = hello?.horizon_ms ?? 3000;
  const lead = frontier_ms - playhead;
  const end = hello?.duration_ms ?? 0;

  // Play only while the computed lead covers the ghost's horizon (projection, ADR-0030).
  if (!playing && (lead >= horizon || (!computing && lead > 0))) playing = true;
  if (playing && computing && lead <= 1) playing = false;
  if (playing) playhead = Math.min(playhead + dt, frontier_ms);
  const ended = !computing && end > 0 && playhead >= end;

  arena.draw(run, playhead);
  const fired = brain.draw(run, playhead, { faint: css("--text-muted"), gold: css("--gold") });

  $("clock").textContent = clock(playhead);
  $("state").textContent = !connected ? "○ offline" : ended ? "■ ended" : playing ? "● live" : "◌ computing ahead";
  $("state").dataset.mode = !connected ? "off" : playing ? "live" : "wait";
  $("brain-note").textContent = fired ? `${fired.toLocaleString()} neurons fired in this 100 ms` : "quiet";
  $("horizon").textContent = `${(horizon / 1000).toFixed(1)} s`;
  // Count only what has been watched (issue #14, B7).
  const { compared, matched } = run.matchUpTo(playhead);
  $("match").textContent = compared ? `${((100 * matched) / compared).toFixed(3)}%` : "—";
  $("checked").textContent = `${compared.toLocaleString()} ms`;
  const ghost = run.ghostFor(playhead);
  $("ghost-from").textContent = ghost ? `t = ${clock(ghost.from_ms)}` : "computing";
  $("lead").textContent = computing ? `${(Math.max(0, lead) / 1000).toFixed(1)} s` : "all computed";
  $("status").textContent = run.status.error
    ? `error: ${run.status.error}`
    : run.status.cached
    ? `replaying a computed run · ${hello?.arena_name ?? ""} dish · seed ${hello?.seed ?? ""}`
    : `computed ${clock(frontier_ms)} of ${clock(end)} · ${hello?.arena_name ?? ""} dish · seed ${hello?.seed ?? ""}`;
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
