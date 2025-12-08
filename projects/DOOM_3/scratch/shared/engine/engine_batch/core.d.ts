export type EngineState = {
  running: boolean;
  tick: number;
  fps: number;
  lastTickMs?: number;
}

export class EngineCore {
  private running: boolean;
  private tickCount: number;
  private fps: number;
  private lastTickMs?: number;
  constructor();
  start(): Promise<EngineState>;
  tick(deltaTimeMs: number): Promise<EngineState>;
  stop(): void;
  status(): EngineState;
}
