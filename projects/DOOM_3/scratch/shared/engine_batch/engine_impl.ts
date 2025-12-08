import { createStore } from '../server'
import type { InMemoryStore } from '../server'
import type { LevelState } from '../models'

export type EngineState = {
  running: boolean
  tick: number
  fps: number
  lastTickMs?: number
}

export class EngineBatch {
  private store: InMemoryStore
  private running: boolean = false
  private tickCount: number = 0
  private fps: number = 0
  private lastTickMs?: number
  private gravity: number = 9.81

  constructor(store?: InMemoryStore) {
    this.store = store ?? createStore()
  }

  public async start(): Promise<EngineState> {
    this.running = true
    this.lastTickMs = Date.now()
    return this.status()
  }

  public async tick(deltaTimeMs: number): Promise<EngineState> {
    const dt = Math.max(0, deltaTimeMs) / 1000
    const levels = Object.values(this.store.levels || {})
    for (const lvl of levels) {
      if (!lvl || !lvl.players) continue
      for (const pid of Object.keys(lvl.players)) {
        const player: any = (lvl.players as any)[pid]
        if (!player) continue
        if (typeof player.y !== 'number') player.y = 0
        if (typeof player.x !== 'number') player.x = 0
        player.y += this.gravity * dt
        const floor = (lvl.height ?? 0) - 1
        if (player.y > floor) player.y = floor
      }
    }
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

  public getWorldState(): any {
    return { levels: this.store.levels }
  }

  public async step(): Promise<EngineState> {
    const DEFAULT_DT = 16
    return this.tick(DEFAULT_DT)
  }
}

export { LevelState } from '../models'
