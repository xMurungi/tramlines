import "./styles/tokens.css";
import "./styles/viewer.css";
import { ArenaView, branchColor } from "./arena";
import { BrainView } from "./brainView";
import { CONTROL, type Fan, type FanBranch, type KnowledgeOption, Run } from "./model";
import { connect } from "./socket";

const run = new Run();
const arena = new ArenaView(document.querySelector<HTMLCanvasElement>("#arena")!);
const brain = new BrainView(document.querySelector<HTMLCanvasElement>("#brain")!);
const $ = (id: string) => document.getElementById(id)!;
const css = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

// A link can open a setting at a moment: ?knowledge=voltage-0.1&t=1200 (ms), and a fan: &fan=1200.
const query = new URLSearchParams(location.search);

let connected = false;
let playhead = Math.max(0, Number(query.get("t")) || 0); // ms of simulated time on screen
let playing = false;
let last = performance.now();
let knowledge = query.get("knowledge") ?? CONTROL; // the setting being watched (ADR-0042)
let stopsFor: KnowledgeOption[] | null = null; // the options the stops were built from
let fanAt: number | null = query.has("fan") ? Math.max(1, Number(query.get("fan")) || 1) : null; // ADR-0046
let fanDrawn = ""; // what the fan panel was last built from

const wire = connect(
  (message) => run.accept(message),
  (open) => {
    connected = open;
    if (open) choose(knowledge); // a (re)connection forgets nothing the viewer asked for
    if (open && fanAt !== null) wire.send({ type: "free_will", at_ms: fanAt });
  },
);

function choose(id: string): void {
  knowledge = id;
  wire.send({ type: "choose", knowledge: id, from_ms: Math.floor(playhead) });
}

$("replay").addEventListener("click", () => {
  playhead = 0;
  playing = false;
  fanAt = null;
  choose(knowledge);
});

// Free will (ADR-0046): fork the moment on screen into futures one extra spike apart.
$("free-will").addEventListener("click", () => {
  fanAt = Math.max(1, Math.floor(playhead));
  wire.send({ type: "free_will", at_ms: fanAt });
});
$("fan-close").addEventListener("click", () => {
  fanAt = null;
});

const BARS = "▁▂▃▄▅▆▇█";

/** Spike differences per bin as bars on a log scale shared by the fan; "·" is exactly none. */
function spark(values: number[], max: number): string {
  const top = Math.log10(1 + max);
  return values
    .map((v) => (v === 0 || top === 0 ? "·" : BARS[Math.min(7, Math.max(0, Math.ceil((7 * Math.log10(1 + v)) / top)))]))
    .join("");
}

function seconds(ms: number): string {
  return `${(ms / 1000).toFixed(2)} s`;
}

/** One branch, in words: where its spike went, what the fly did, whether the brain forgot. */
function branchRow(branch: FanBranch | undefined, index: number, fan: Fan, sparkMax: number): HTMLLIElement {
  const li = document.createElement("li");
  li.className = "branch";
  const num = document.createElement("span");
  num.className = "num";
  const swatch = document.createElement("span");
  swatch.className = "swatch";
  const hue = branchColor(index);
  swatch.style.background = hue;
  swatch.style.color = hue;
  num.append(swatch, String(index + 1));
  const who = document.createElement("span");
  who.className = "who";
  who.textContent = `spike in ${fan.aimed[index]?.label ?? "…"}`;
  const what = document.createElement("span");
  what.className = "what";
  const spike = document.createElement("span");
  spike.className = "spark";
  if (!branch) {
    li.classList.add("waiting");
    what.textContent = "computing…";
    li.append(num, who, what);
    return li;
  }
  const body = !branch.split
    ? "never left the untouched path"
    : branch.body_rejoined
    ? `split at ${branch.first_apart_ms} ms, back on the path by the end`
    : `split at ${branch.first_apart_ms} ms · ${branch.end_distance_mm.toFixed(2)} mm apart at the end`;
  const acts = branch.events.map(([t, e]) => `${e} at +${seconds(t - fan.at_ms)}`).join(", ");
  const brain = branch.brain_rejoined ? "brain forgot the spike" : "brain still different";
  what.textContent = `${body}${acts ? ` · ${acts}` : ""} · ${brain}`;
  swatch.dataset.forGood = String(branch.split && !branch.body_rejoined);
  spike.textContent = spark(branch.spike_diffs, sparkMax);
  const total = branch.spike_diffs.reduce((a, b) => a + b, 0);
  spike.title = `${total.toLocaleString()} spikes differ in ${seconds(fan.horizon_ms)}; per ${branch.spike_bin_ms} ms: ${branch.spike_diffs.join(", ")}`;
  spike.setAttribute("aria-label", spike.title);
  li.append(num, who, what, spike);
  return li;
}

/** The free-will panel and the footer meter, rebuilt only when the fan changes. */
function drawFanPanel(): void {
  const fan = fanAt === null ? undefined : run.fans.get(fanAt);
  const branches = fan ? run.branches.get(fan.at_ms) ?? [] : [];
  const made = branches.filter(Boolean) as FanBranch[];
  const key = fanAt === null ? "" : JSON.stringify([fan ?? fanAt, made.length, run.status.fans_to_compute]);
  if (key === fanDrawn) return;
  fanDrawn = key;
  $("fan-panel").hidden = fanAt === null;
  $("fan-meter").hidden = !made.length;
  if (fanAt === null) return;
  $("fan-title").textContent = `t = ${clock(fanAt)}${fan?.decision ? ` · ${fan.decision}` : ""}`;
  const list = $("fan-branches");
  if (!fan || fan.not_made) {
    $("fan-note").textContent = fan?.not_made ? `No fan: ${fan.not_made}.` : "Asking the ghost process…";
    list.replaceChildren();
    return;
  }
  const n = fan.aimed.length;
  const parts: string[] = [];
  if (fan.driven === null) parts.push(`Waiting for the ghost process (${run.status.fans_to_compute} fan${run.status.fans_to_compute === 1 ? "" : "s"} to compute; ghosts wait meanwhile).`);
  else {
    parts.push(`${fan.done ? n : `${made.length} of ${n}`} futures, ${seconds(fan.horizon_ms)} each. Each got one extra spike in a different neuron receiving input (${fan.driven} at this moment), added at exactly this moment; the rest of each brain is the live one.`);
    if (n < fan.wanted) parts.push(`Only ${n} of the ${fan.wanted} asked for could be made here.`);
    if (fan.refused.length) {
      const why = [...new Set(fan.refused.map((r) => r.reason.replace(/^neuron \d+ /, "")))].join("; ");
      parts.push(`${fan.refused.length} refused by the engine (${why}); the next candidate took each one's place.`);
    }
    if (fan.base_compared_ms) parts.push(`The untouched future, computed separately: ${fan.base_matched_ms.toLocaleString()} / ${fan.base_compared_ms.toLocaleString()} ms identical to the live fly.`);
  }
  $("fan-note").textContent = parts.join(" ");
  const sparkMax = Math.max(0, ...made.flatMap((b) => b.spike_diffs));
  list.replaceChildren(...fan.aimed.map((_, i) => branchRow(branches[i], i, fan, sparkMax)));

  // Footer (CLAUDE.md 9.3): how many futures are apart from the untouched one, over the horizon.
  if (made.length) {
    const bins = 10;
    const per = Math.max(1, Math.floor(made[0].distance_mm.length / bins));
    const apart = Array.from({ length: bins }, (_, k) => made.filter((b) => (b.distance_mm[(k + 1) * per - 1] ?? 0) > (run.hello?.right_within_mm ?? 0.1)).length);
    const bars = apart.map((a) => (a ? BARS[Math.min(7, Math.ceil((7 * a) / made.length))] : "·")).join("");
    const meter = $("fan-meter");
    meter.replaceChildren(`branches: ${made.length} · apart `, Object.assign(document.createElement("span"), { className: "bars", textContent: bars }));
    meter.setAttribute("aria-label", `futures apart from the untouched one at each tenth of the horizon: ${apart.join(", ")} of ${made.length}`);
    meter.title = meter.getAttribute("aria-label")!;
  }
}

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

/**
 * Result 1's counts for this stop, so one example on screen is not taken for the rule
 * (owner decision 24; ADR-0038): the same error can succeed or fail by chance.
 */
function evidence(setting: KnowledgeOption | undefined): string {
  const counts = setting?.result1 ?? [];
  if (!counts.length) return "";
  const parts = counts.map((c) => `${c.moment} ${c.right}/${c.total}`).join(" · ");
  return setting?.id === CONTROL
    ? `Result 1: right every time (${parts}), as a copy must be.`
    : `Result 1, this dish, 3 seeds × 3 draws: right for all 3 s in ${parts}. The ghost on screen is one draw.`;
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

  arena.draw(run, playhead, knowledge, label, fanAt, now);
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
  $("knowledge-evidence").textContent = evidence(setting);
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

  // Free will is offered only where the world is asking the brain something (ADR-0031, 0032).
  const decision = run.decisionAt(playhead);
  const offered = connected && Boolean(decision) && playhead >= 1 && Boolean(run.checkpointFor(playhead));
  const button = $("free-will") as HTMLButtonElement;
  button.disabled = !offered;
  button.title = offered
    ? `${decision}: fork this moment into futures, each one extra spike apart`
    : "Free will is offered at decision moments: on food or bitter, or a shadow approaching. Elsewhere one extra spike almost never changes anything in this model.";
  drawFanPanel();
  $("lead").textContent = computing ? `${(Math.max(0, lead) / 1000).toFixed(1)} s` : "all computed";
  $("status").textContent = run.status.error
    ? `error: ${run.status.error}`
    : run.status.cached
    ? `replaying a computed run · ${hello?.arena_name ?? ""} dish · seed ${hello?.seed ?? ""}`
    : `computed ${clock(frontier_ms)} of ${clock(end)} · ${hello?.arena_name ?? ""} dish · seed ${hello?.seed ?? ""}`;
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
