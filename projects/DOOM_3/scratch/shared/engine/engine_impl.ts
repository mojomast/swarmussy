import { World } from '../world';
import type { EngineState, Engine } from './engine'

export class EngineImpl implements Engine {
  private world: World
  private dtMs: number
  private running = false
  private state: EngineState

  constructor(world: World, dtMs: number = 16) {
    this.world = world
    this.dtMs = dtMs
    this.state = {
      running: false,
      tick: 0,
      fps: 0,
      lastTickMs: undefined,
    }
  }

  public async start(): Promise<EngineState> {
    if (this.state.running) return this.state
    this.running = true
    this.state.running = true
    this.state.lastTickMs = Date.now()
    return this.state
  }

  public async tick(): Promise<EngineState> {
    if (!this.running) {
      this.running = true
      this.state.running = true
      this.state.lastTickMs = Date.now()
    }
    const dtSec = Math.max(0, this.dtMs) / 1000
    this.world.step(dtSec)
    this.state.tick += 1
    const now = Date.now()
    if (this.state.lastTickMs) {
      const delta = now - this.state.lastTickMs
      if (delta > 0) this.state.fps = Math.round(1000 / delta)
    }
    this.state.lastTickMs = now
    return this.state
  }

  public stop(): void {
    this.running = false
    this.state.running = false
  }

  public status(): EngineState {
    return this.state
  }

  public getWorldState(): any {
    return this.world.getState()
  }
}
