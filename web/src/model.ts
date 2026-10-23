// What the viewer knows about the run, assembled from the server's messages (ADR-0033).

export type PoseRow = [number, number, number, number, boolean, boolean]; // t, x, y, heading, feeding, jumped

export interface Patch { x_mm: number; y_mm: number; radius_mm: number; kind: "food" | "bitter"; strength: number }
export interface Loom { start_ms: number; duration_ms: number; direction_rad: number; strength: number }

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
}

export interface Chunk { type: "chunk"; t0_ms: number; poses: PoseRow[]; fired: string; spikes: number }
export interface Ghost { type: "ghost"; from_ms: number; poses: PoseRow[] }
export interface Match {
  type: "match";
  compared_ms: number;
  matched_ms: number;
  by_second: [number, number, number][]; // second, compared, matched
}
export interface Status {
  type: "status";
  frontier_ms: number;
  ghost_checkpoint_ms: number | null;
  computing: boolean;
  cached: boolean;
  error: string | null;
}
export type Message = Hello | Chunk | Ghost | Match | Status;

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
  ghosts: Ghost[] = []; // in order of from_ms, one per checkpoint
  match: Match = { type: "match", compared_ms: 0, matched_ms: 0, by_second: [] };
  status: Status = {
    type: "status",
    frontier_ms: 0,
    ghost_checkpoint_ms: null,
    computing: true,
    cached: false,
    error: null,
  };

  accept(message: Message): void {
    switch (message.type) {
      case "hello": {
        // A (re)connection replays the whole run: start clean so nothing is counted twice
        // (issue #14, B8).
        this.poses = [];
        this.firedByChunk.clear();
        this.ghosts = [];
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
      case "ghost":
        this.ghosts = this.ghosts.filter((g) => g.from_ms !== message.from_ms);
        this.ghosts.push(message);
        this.ghosts.sort((a, b) => a.from_ms - b.from_ms);
        break;
      case "match":
        this.match = message;
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
  matchUpTo(t: number): { compared: number; matched: number } {
    let compared = 0;
    let matched = 0;
    for (const [second, c, m] of this.match.by_second) {
      if ((second + 1) * 1000 > t) continue; // that second has not been fully watched yet
      compared += c;
      matched += m;
    }
    return { compared, matched };
  }

  /** The ghost prediction made from the latest checkpoint at or before `t`. */
  ghostFor(t: number): Ghost | undefined {
    let best: Ghost | undefined;
    for (const g of this.ghosts) if (g.from_ms <= t) best = g;
    return best;
  }
}
