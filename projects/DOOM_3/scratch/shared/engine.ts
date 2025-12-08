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
}
