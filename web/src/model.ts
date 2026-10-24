// What the viewer knows about the run, assembled from the server's messages (ADR-0033, ADR-0042).

export type PoseRow = [number, number, number, number, boolean, boolean]; // t, x, y, heading, feeding, jumped

export interface Patch { x_mm: number; y_mm: number; radius_mm: number; kind: "food" | "bitter"; strength: number }
export interface Loom { start_ms: number; duration_ms: number; direction_rad: number; strength: number }

export interface KnowledgeOption { id: string; label: string; description: string; needs_spike_in_transit: boolean }

export const CONTROL = "control";

export interface Hello {
  type: "hello";
  arena_name: string;
  radius_mm: number;
  patches: Patch[];
  looms: Loom[];
  seed: number;
  horizon_ms: number;
  duration_ms: number;
  n_neurons: number;
  neuron_xy: string;
  knowledge: KnowledgeOption[]; // the slider's stops, in order
  right_within_mm: number; // "on path" for an imperfect ghost (Result 1)
}

export interface Chunk { type: "chunk"; t0_ms: number; poses: PoseRow[]; fired: string; spikes: number }
export interface Checkpoint { type: "checkpoint"; at_ms: number; in_flight: number }
export interface Ghost { type: "ghost"; knowledge: string; from_ms: number; poses: PoseRow[] }
export interface Refused { type: "refused"; knowledge: string; from_ms: number; reason: string }
export interface Match {
  type: "match";
  knowledge: string;
  compared_ms: number;
  matched_ms: number; // bit for bit
  close_ms: number; // within right_within_mm
  by_second: [number, number, number, number][]; // second, compared, matched, close
  right_for: [number, number][]; // from_ms, ms on path (once the whole horizon is checked)
}
export interface Status {
  type: "status";
  frontier_ms: number;
  ghost_checkpoint_ms: number | null;
  computing: boolean;
  cached: boolean;
  error: string | null;
  to_compute: Record<string, number>; // chosen setting -> ghosts still to compute
}
export type Message = Hello | Chunk | Checkpoint | Ghost | Refused | Match | Status;

/** The one message a viewer sends: which knowledge setting to watch, from about when. */
export interface Choose { type: "choose"; knowledge: string; from_ms: number }

function decodeBase64(text: string): Uint8Array {
  const raw = atob(text);
  const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
  return bytes;
}

export class Run {
  hello: Hello | null = null;
  neuronXY: Uint16Array = new Uint16Array(0); // x0, y0, x1, y1, ...
  poses: (PoseRow | undefined)[] = []; // indexed by time_ms
  firedByChunk = new Map<number, Uint32Array>(); // chunk start ms -> neurons that fired
  checkpoints: Checkpoint[] = []; // in order of at_ms
  ghosts = new Map<string, Ghost[]>(); // setting -> ghosts in order of from_ms
  refused = new Map<string, Map<number, string>>(); // setting -> from_ms -> reason
  matches = new Map<string, Match>(); // setting -> its latest scores
  status: Status = {
    type: "status",
    frontier_ms: 0,
    ghost_checkpoint_ms: null,
    computing: true,
    cached: false,
    error: null,
    to_compute: {},
  };

  accept(message: Message): void {
    switch (message.type) {
      case "hello": {
        // A (re)connection replays the whole run: start clean so nothing is counted twice
        // (issue #14, B8).
        this.poses = [];
        this.firedByChunk.clear();
        this.checkpoints = [];
        this.ghosts.clear();
        this.refused.clear();
        this.matches.clear();
        this.hello = message;
        const bytes = decodeBase64(message.neuron_xy);
        this.neuronXY = new Uint16Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 2);
        break;
      }
      case "chunk":
        for (const row of message.poses) this.poses[row[0]] = row;
        {
          const bytes = decodeBase64(message.fired);
          this.firedByChunk.set(message.t0_ms, new Uint32Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 4));
        }
        break;
      case "checkpoint":
        this.checkpoints = this.checkpoints.filter((c) => c.at_ms !== message.at_ms);
        this.checkpoints.push(message);
        this.checkpoints.sort((a, b) => a.at_ms - b.at_ms);
        break;
      case "ghost": {
        const list = (this.ghosts.get(message.knowledge) ?? []).filter((g) => g.from_ms !== message.from_ms);
        list.push(message);
        list.sort((a, b) => a.from_ms - b.from_ms);
        this.ghosts.set(message.knowledge, list);
        break;
      }
      case "refused": {
        const reasons = this.refused.get(message.knowledge) ?? new Map<number, string>();
        reasons.set(message.from_ms, message.reason);
        this.refused.set(message.knowledge, reasons);
        break;
      }
      case "match":
        this.matches.set(message.knowledge, message);
        break;
      case "status":
        this.status = message;
        break;
    }
  }

  /** The most recent pose at or before `t`. */
  poseAt(t: number): PoseRow | undefined {
    for (let k = Math.floor(t); k >= 0 && k > t - 200; k--) {
      const p = this.poses[k];
      if (p) return p;
    }
    return undefined;
  }

  /** Ghost-versus-live milliseconds checked so far, counting only seconds already played. */
  matchUpTo(t: number, knowledge: string): { compared: number; matched: number; close: number } {
    let compared = 0;
    let matched = 0;
    let close = 0;
    for (const [second, c, m, n] of this.matches.get(knowledge)?.by_second ?? []) {
      if ((second + 1) * 1000 > t) continue; // that second has not been fully watched yet
      compared += c;
      matched += m;
      close += n;
    }
    return { compared, matched, close };
  }

  /** The latest saved moment at or before `t`: where the ghost on screen should start. */
  checkpointFor(t: number): Checkpoint | undefined {
    let best: Checkpoint | undefined;
    for (const c of this.checkpoints) if (c.at_ms <= t) best = c;
    return best;
  }

  /** The prediction made from the latest checkpoint at or before `t` that has one. */
  ghostFor(t: number, knowledge: string): Ghost | undefined {
    let best: Ghost | undefined;
    for (const g of this.ghosts.get(knowledge) ?? []) if (g.from_ms <= t) best = g;
    return best;
  }

  /** Why no ghost could start from the moment behind `t`, if it was refused. */
  refusalFor(t: number, knowledge: string): string | undefined {
    const moment = this.checkpointFor(t);
    return moment ? this.refused.get(knowledge)?.get(moment.at_ms) : undefined;
  }

  /** How long the ghost from `from_ms` stayed on the live path, once that is known. */
  rightFor(knowledge: string, from_ms: number): number | undefined {
    return this.matches.get(knowledge)?.right_for.find(([from]) => from === from_ms)?.[1];
  }
}
