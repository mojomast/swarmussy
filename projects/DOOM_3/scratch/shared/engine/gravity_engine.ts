export interface WorldLike {
  getWorldState(): any
  step(dt: number): void
  reset(): void
}

export type EngineState = {
  running: boolean
  tick: number
  fps: number
  lastTickMs?: number
}

export class GravityEngine {
  private world: WorldLike
  private dtMs: number
  private running = false
  private tickCount = 0
  private fps = 0
  private lastTickMs?: number

  constructor(world: WorldLike, dtMs: number = 16) {
    this.world = world
    this.dtMs = dtMs
  }

  public async start(): Promise<EngineState> {
    this.running = true
    this.lastTickMs = Date.now()
    return this.status()
  }

  public async tick(): Promise<EngineState> {
    const dtSec = Math.max(0, this.dtMs) / 1000
    this.world.step(dtSec)
    this.tickCount += 1
    const now = Date.now()
    if (this.lastTickMs) {
      const dt = now - this.lastTickMs
      if (dt > 0) this.fps = Math.round(1000 / dt)
    }
    this.lastTickMs = now
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

  public getWorldState(): any {
    return this.world.getWorldState()
  }
}
