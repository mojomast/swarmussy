export interface EngineState {
  running: boolean
  tick: number
  fps: number
  lastTickMs?: number
}

export interface Engine {
  start(): Promise<EngineState>
  tick(deltaTimeMs: number): Promise<EngineState>
  stop(): void
  getWorldState(): any
  step(): Promise<EngineState>
}

export class GravityEngine implements Engine {
  private world: any
  private running = false
  private tickCount = 0
  private gravity = 9.81

  constructor(world?: any) {
    this.world = world ?? { levels: {} }
  }

  async start(): Promise<EngineState> {
    this.running = true
    return this.status()
  }

  async tick(deltaTimeMs: number): Promise<EngineState> {
    const dt = Math.max(0, deltaTimeMs) / 1000
    for (const lvl of Object.values(this.world.levels)) {
      const players = lvl?.players || {}
      for (const p of Object.values(players)) {
        p.y = (p.y ?? 0) + this.gravity * dt
      }
    }
    this.tickCount++
    this.lastTickMs = Date.now()
    return this.status()
  }

  stop(): void {
    this.running = false
  }

  private lastTickMs?: number

  private status(): EngineState {
    return {
      running: this.running,
      tick: this.tickCount,
      fps: 0,
      lastTickMs: this.lastTickMs
    }
  }

  getWorldState() {
    return this.world
  }

  async step(): Promise<EngineState> {
    return this.tick(16)
  }
}
