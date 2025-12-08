import { Engine, EngineState } from '../engine';
import { store } from '../store';
import { LevelState, PlayerState } from '../models';

// Minimal ECS-like engine core skeleton tied to the in-memory store
// This is designed for integration tests and as a scaffold for the full engine
export class EngineCore implements Engine {
  private interval?: NodeJS.Timeout;
  private state: EngineState;
  private gravity: number;
  private storeRef: { levels: Record<string, LevelState> };

  constructor(storeOverride?: { levels: Record<string, LevelState> }) {
    this.gravity = 1; // deterministic gravity per tick for tests
    this.storeRef = storeOverride ?? store;

    this.state = {
      running: false,
      tick: 0,
      fps: 0,
      lastTickMs: undefined,
    };
  }

  private step(): void {
    // Ensure at least one level exists in store for the demo
    const levels = Object.values(this.storeRef.levels);
    for (const lvl of levels) {
      // apply a simple gravity to each player
      for (const pid of Object.keys(lvl.players)) {
        const p = lvl.players[pid] as PlayerState;
        // simple gravity: pull downward by fixed amount
        p.y = (p.y ?? 0) + this.gravity;
        // clamp to floor
        if (p.y > lvl.height - 1) p.y = lvl.height - 1;
      }
    }
  }

  public async start(): Promise<EngineState> {
    if (this.state.running) return this.state;
    this.state.running = true;

    // Start a simple interval loop
    const tickMs = 16; // ~60fps
    let last = Date.now();
    this.state.lastTickMs = last;
    this.interval = setInterval(() => {
      const now = Date.now();
      const dt = Math.max(0, now - last);
      last = now;
      this.state.tick += 1;
      this.state.lastTickMs = now;
      // crude fps estimate
      if (dt > 0) {
        this.state.fps = Math.round(1000 / dt);
      }
      this.step();
    }, tickMs) as unknown as NodeJS.Timeout;
    return this.state;
  }

  public async tick(): Promise<EngineState> {
    // One manual tick; calculate delta since lastTickMs if available
    const now = Date.now();
    const delta = this.state.lastTickMs ? now - this.state.lastTickMs : 16;
    this.state.tick += 1;
    this.state.lastTickMs = now;
    if (delta > 0) {
      this.state.fps = Math.round(1000 / delta);
    } else {
      this.state.fps = 60;
    }
    this.step();
    return this.state;
  }

  public stop(): void {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = undefined;
    }
    this.state.running = false;
  }

  public status(): EngineState {
    return this.state;
  }

  private applyGravity(): void {
    // Iterate all levels and apply a simple gravity step to every player
    const levels: LevelState[] = Object.values(this.storeRef.levels);
    for (const lvl of levels) {
      for (const pid of Object.keys(lvl.players)) {
        const p = lvl.players[pid] as PlayerState;
        // simple gravity: pull downward by fixed amount
        p.y = (p.y ?? 0) + this.gravity;
        // clamp to floor
        if (p.y > lvl.height - 1) p.y = lvl.height - 1;
      }
    }
  }
}

export default EngineCore;
