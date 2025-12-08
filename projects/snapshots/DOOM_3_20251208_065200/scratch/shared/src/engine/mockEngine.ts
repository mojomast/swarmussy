import { Engine, EngineState } from './engine'

// Lightweight in-memory mock engine used for UI integration tests
export class MockEngine implements Engine {
  private running = false
  private tickValue = 0
  private lastTickMs?: number
  private fps = 60

  async start(): Promise<EngineState> {
    this.running = true
    this.tickValue = 0
    this.lastTickMs = undefined
    this.fps = 60
    return this.status()
  }

  async tick(): Promise<EngineState> {
    if (!this.running) {
      return this.status()
    }
    // simulate a fixed delta per tick
    const delta = 16
    this.tickValue += 1
    this.lastTickMs = delta
    // keep FPS stable for the mock
    this.fps = 60
    return this.status()
  }

  stop(): void {
    this.running = false
  }

  status(): EngineState {
    return {
      running: this.running,
      tick: this.tickValue,
      fps: this.fps,
      lastTickMs: this.lastTickMs,
    }
  }
}
