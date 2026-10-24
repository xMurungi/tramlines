import "./styles/tokens.css";
import "./styles/viewer.css";
import { ArenaView } from "./arena";
import { BrainView } from "./brainView";
import { CONTROL, type KnowledgeOption, Run } from "./model";
import { connect } from "./socket";

const run = new Run();
const arena = new ArenaView(document.querySelector<HTMLCanvasElement>("#arena")!);
const brain = new BrainView(document.querySelector<HTMLCanvasElement>("#brain")!);
const $ = (id: string) => document.getElementById(id)!;
const css = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

// A link can open a setting at a moment: ?knowledge=voltage-0.1&t=1200 (ms).
const query = new URLSearchParams(location.search);

let connected = false;
let playhead = Math.max(0, Number(query.get("t")) || 0); // ms of simulated time on screen
let playing = false;
let last = performance.now();
let knowledge = query.get("knowledge") ?? CONTROL; // the setting being watched (ADR-0042)
let stopsFor: KnowledgeOption[] | null = null; // the options the stops were built from

const wire = connect(
  (message) => run.accept(message),
  (open) => {
    connected = open;
    if (open) choose(knowledge); // a (re)connection forgets nothing the viewer asked for
  },
);

function choose(id: string): void {
  knowledge = id;
  wire.send({ type: "choose", knowledge: id, from_ms: Math.floor(playhead) });
}

$("replay").addEventListener("click", () => {
  playhead = 0;
  playing = false;
  choose(knowledge);
});

/** One radio per stop, built from the server's list so the two never disagree. */
function buildStops(options: KnowledgeOption[]): void {
  const group = $("knowledge");
  group.replaceChildren(
    ...options.map((option) => {
      const label = document.createElement("label");
      label.className = "stop";
      label.title = option.description;
      const input = document.createElement("input");
      input.type = "radio";
      input.name = "knowledge";
      input.value = option.id;
      input.checked = option.id === knowledge;
      input.addEventListener("change", () => choose(option.id));
      label.append(input, option.id === CONTROL ? "everything (control)" : option.label);
      return label;
    }),
  );
  stopsFor = options;
}

/** "One missed spike" is offered only when the moment behind the playhead has one in transit. */
function updateStops(options: KnowledgeOption[]): boolean {
  const quiet = run.checkpointFor(playhead)?.in_flight === 0;
  for (const input of $("knowledge").querySelectorAll<HTMLInputElement>("input")) {
    const option = options.find((o) => o.id === input.value);
    input.disabled = Boolean(option?.needs_spike_in_transit && quiet);
    input.parentElement!.title = input.disabled
      ? "no spike is in transit at this moment: there is nothing to miss"
      : option?.description ?? "";
  }
  return quiet;
}

function clock(ms: number): string {
  const s = Math.max(0, ms) / 1000;
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${(s % 60).toFixed(3).padStart(6, "0")}`;
}

const percent = (part: number, whole: number) => (whole ? `${((100 * part) / whole).toFixed(3)}%` : "—");

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

  const options = hello?.knowledge ?? [];
  if (hello && !options.some((o) => o.id === knowledge)) choose(CONTROL); // an unknown link
  if (hello && stopsFor !== options) buildStops(options);
  const quiet = updateStops(options);
  const setting = options.find((o) => o.id === knowledge);
  const isControl = knowledge === CONTROL;
  const label = isControl ? "control" : setting?.label ?? knowledge;

  arena.draw(run, playhead, knowledge, label);
  const fired = brain.draw(run, playhead, { faint: css("--text-muted"), gold: css("--gold") });

  $("clock").textContent = clock(playhead);
  $("state").textContent = !connected ? "○ offline" : ended ? "■ ended" : playing ? "● live" : "◌ computing ahead";
  $("state").dataset.mode = !connected ? "off" : playing ? "live" : "wait";
  $("brain-note").textContent = fired ? `${fired.toLocaleString()} neurons fired in this 100 ms` : "quiet";
  $("horizon").textContent = `${(horizon / 1000).toFixed(1)} s`;

  // What this ghost is, said plainly (ADR-0035): the control copies, it does not predict.
  $("ghost-kind").textContent = isControl ? "the control" : `imperfect ghost · ${label}`;
  $("ghost-kind").dataset.control = String(isControl);
  $("knowledge-note").textContent = isControl
    ? "Everything: the ghost is a bit-exact copy of the live brain."
    : `${setting?.description ?? ""}. The body and the senses are known exactly; only the brain is measured.`;
  const within = hello?.right_within_mm ?? 0.1;
  $("ghost-note").textContent = isControl
    ? "A separate process restarts the brain from a saved moment with the same code and the same random numbers. It is always right because the simulation is deterministic: that is copying, not predicting. It is here as the control."
    : `Every second this ghost starts again from the live brain, measured imperfectly, and runs ahead on its own. On path: within ${within} mm of the live fly (Result 1's test). Where it leaves the path it is drawn in rose.`;

  // Count only what has been watched (issue #14, B7).
  const { compared, matched, close } = run.matchUpTo(playhead, knowledge);
  $("match").textContent = percent(matched, compared);
  $("on-path").textContent = percent(close, compared);
  $("checked").textContent = `${compared.toLocaleString()} ms`;

  const refusal = run.refusalFor(playhead, knowledge);
  const ghost = refusal ? undefined : run.ghostFor(playhead, knowledge);
  const waiting = run.status.to_compute[knowledge];
  let thisGhost: string;
  if (refusal) thisGhost = "not made";
  else if (!ghost) thisGhost = waiting ? `computing · ${waiting} to go` : "computing";
  else {
    const rightFor = run.rightFor(knowledge, ghost.from_ms);
    const age = playhead - ghost.from_ms - 1;
    if (rightFor !== undefined && age >= rightFor && rightFor < horizon) thisGhost = `peeled away after ${rightFor} ms`;
    else if (rightFor !== undefined && rightFor >= horizon && age >= horizon) thisGhost = `right for all ${(horizon / 1000).toFixed(1)} s`;
    else thisGhost = "on path so far";
  }
  $("this-ghost").textContent = thisGhost;
  if (refusal) {
    $("ghost-note").textContent = `No ghost from this moment: ${refusal}.`;
  } else if (setting?.needs_spike_in_transit && quiet) {
    $("ghost-note").textContent = "No spike is in transit at this moment, so there is nothing to miss.";
  }

  $("ghost-from").textContent = ghost ? `t = ${clock(ghost.from_ms)}` : "—";
  $("lead").textContent = computing ? `${(Math.max(0, lead) / 1000).toFixed(1)} s` : "all computed";
  $("status").textContent = run.status.error
    ? `error: ${run.status.error}`
    : run.status.cached
    ? `replaying a computed run · ${hello?.arena_name ?? ""} dish · seed ${hello?.seed ?? ""}`
    : `computed ${clock(frontier_ms)} of ${clock(end)} · ${hello?.arena_name ?? ""} dish · seed ${hello?.seed ?? ""}`;
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
