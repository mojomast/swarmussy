// Browser-side shim that mimics Engine interface from scratch/shared/engine.ts
export class EngineShim {
  constructor() {
    this._started = false;
    this._tick = 0;
  }
  async start() {
    this._started = true;
  }
  async stop() {
    this._started = false;
  }
  async tick() {
    // simple tick progression
    this._tick += 1;
    const dt = 16;
    return { dt, tick: this._tick };
  }
  getState() {
    return { started: this._started, tick: this._tick };
  }
}
