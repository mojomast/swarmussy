// Engine implementation skeleton for DI/testing (standalone)
// This module provides a minimal, fully-typed Engine API that can be used by tests
// and by other components while scratch/shared/engine.ts remains locked for now.

export type EngineState = {
  running: boolean
  tick: number
  fps: number
  lastTickMs?: number
}

export interface Engine {
  start(): Promise<EngineState>
  tick(): Promise<EngineState>
  stop(): void
  status(): EngineState
  getWorldState(): World
  step(): Promise<World>
  reset(): Promise<World>
}

// Basic ECS-ish definitions
export interface Entity {
  id: string
  components: { [key: string]: any }
}

export interface System {
  update(world: World, deltaMs: number): void
}

export interface World {
  entities: Entity[]
  systems: System[]
  tick: number
}

export interface EngineStore {
  loadWorld(): Promise<World>
  saveWorld(world: World): Promise<void>
  resetWorld(): Promise<World>
}

export interface EngineOptions {
  store?: EngineStore
  gravity?: number
  timeScale?: number
  initialWorld?: World
}

export class EngineImpl implements Engine {
  private _store?: EngineStore
  private _world: World
  private _running: boolean = false
  private _tick: number = 0
  private _fps: number = 0
  private _lastTickMs?: number
  private _lastFpsTime: number = 0
  private _framesThisSecond: number = 0
  private _gravity: number
  private _timeScale: number

  constructor(opts?: EngineOptions) {
    this._store = opts?.store
    this._gravity = opts?.gravity ?? 9.81
    this._timeScale = opts?.timeScale ?? 1
    this._world = opts?.initialWorld ?? { entities: [], systems: [], tick: 0 }
    // ensure world systems array exists
    if (!this._world.systems) {
      this._world.systems = []
    }
  }

  // Allow tests/clients to inject extra systems at runtime
  addSystem(system: System): void {
    this._world.systems.push(system)
  }

  async start(): Promise<EngineState> {
    // Optionally load world from store
    if (this._store) {
      try {
        const w = await this._store.loadWorld()
        if (w) {
          this._world = w
        }
      } catch {
        // ignore load failures, continue with in-memory world
      }
    }
    this._running = true
    this._lastTickMs = undefined
    this._framesThisSecond = 0
    this._lastFpsTime = Date.now()
    return this.status()
  }

  async tick(): Promise<EngineState> {
    if (!this._running) {
      return this.status()
    }
    const now = typeof performance !== 'undefined' && performance.now
      ? performance.now()
      : Date.now()
    const delta = this._lastTickMs != null ? Math.max(0, now - this._lastTickMs) : 16
    this._lastTickMs = now

    // Update all systems
    for (const s of this._world.systems) {
      s.update(this._world, delta * this._timeScale)
    }

    // advance world tick counter
    this._tick += 1
    this._world.tick = this._tick

    // FPS calculation (simple)
    this._framesThisSecond += 1
    if (now - this._lastFpsTime >= 1000) {
      this._fps = this._framesThisSecond
      this._framesThisSecond = 0
      this._lastFpsTime = now
    }

    // Persist world if store provided
    if (this._store) {
      this._store.saveWorld(this._world).catch(() => {})
    }

    return this.status()
  }

  stop(): void {
    this._running = false
  }

  status(): EngineState {
    return {
      running: this._running,
      tick: this._tick,
      fps: this._fps,
      lastTickMs: this._lastTickMs,
    }
  }

  getWorldState(): World {
    return this._world
  }

  async step(): Promise<World> {
    await this.tick()
    return this._world
  }

  async reset(): Promise<World> {
    const newWorld: World = { entities: [], systems: [], tick: 0 }
    this._world = newWorld
    this._tick = 0
    // Try to reset in store as well
    if (this._store) {
      try {
        const w = await this._store.resetWorld()
        if (w) this._world = w
      } catch {
        // ignore
      }
    }
    return this._world
  }
}

export default EngineImpl
