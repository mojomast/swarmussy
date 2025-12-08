import { createStore, InMemoryStore } from './server'
import type { WorldState, WorldEntity } from './engine_batch/core'

// Lightweight bridge engine that operates on the in-memory World provided by server.ts
export type EngineState = {
  running: boolean
  tick: number
  fps: number
  lastTickMs?: number
}

export class EngineBridge {
  private gravity: number
  private running: boolean = false
  private tickCount: number = 0
  private fps: number = 0
  private lastTickMs?: number
  private store: InMemoryStore

  constructor(config?: { gravity?: number; store?: InMemoryStore }) {
    this.gravity = config?.gravity ?? 9.81
    this.store = config?.store ?? createStore()
  }

  // Build a light-weight world view from the in-memory store
  public getWorldState(): WorldState {
    const entities: Map<string, WorldEntity> = new Map()
    for (const lvl of Object.values(this.store.levels)) {
      if (!lvl || !lvl.players) continue
      for (const pid of Object.keys(lvl.players)) {
        const p = (lvl.players[pid] as any) || { x: 0, y: 0 }
        const pos = {
          x: typeof p.x === 'number' ? p.x : 0,
          y: typeof p.y === 'number' ? p.y : 0,
        }
        entities.set(pid, { id: pid, pos, vel: { x: 0, y: 0 } })
      }
    }
    return { entities }
  }

  public async start(): Promise<EngineState> {
    if (this.running) return this.status()
    this.running = true
    this.lastTickMs = Date.now()
    return this.status()
  }

  // Tick with explicit delta in milliseconds and advance world
  public async tick(deltaTimeMs: number = 16.6667): Promise<EngineState> {
    this.step(deltaTimeMs)
    return this.status()
  }

  public step(deltaTimeMs: number = 16.6667): EngineState {
    const dt = deltaTimeMs / 1000
    // Apply gravity-like effect to every player in every level
    for (const lvl of Object.values(this.store.levels)) {
      if (!lvl || !lvl.players) continue
      for (const pid of Object.keys(lvl.players)) {
        const p = (lvl.players[pid] as any) || { x: 0, y: 0 }
        if (typeof p.y !== 'number') p.y = 0
        p.y += this.gravity * dt
        lvl.players[pid] = p
      }
    }
    this.tickCount++
    this.fps = Math.max(1, Math.round(1 / Math.max(0.001, dt)))
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
