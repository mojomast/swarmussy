export type EngineState = {
  running: boolean
  tick: number
  fps: number
  lastTickMs?: number
}

export class EngineBatch {
  private running = false
  private tickCount = 0
  private fps = 0
  private lastTickMs?: number

  constructor() {}

  public async start(): Promise<EngineState> {
    this.running = true
    this.lastTickMs = Date.now()
    return this.status()
  }

  public async tick(deltaTimeMs: number = 16): Promise<EngineState> {
    const dt = Math.max(0, deltaTimeMs) / 1000
    this.tickCount += 1
    this.fps = dt > 0 ? Math.round(1 / dt) : this.fps
    this.lastTickMs = Date.now()
    return this.status()
  }

  public stop(): void {
    this.running = false
  }

  public status(): EngineState {
    return {
      running: this.running,
      tick: this.tickCount,
      fps: this.fps,
      lastTickMs: this.lastTickMs,
    }
  }
}
