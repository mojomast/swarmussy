export interface Engine {
  start(): Promise<any>
  tick(): Promise<any>
  stop(): void
  status(): any
}
