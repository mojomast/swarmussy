export interface EngineInterface {
  start(): Promise<void>
  tick(): Promise<void>
  stop(): void
  state(): any
}
