export interface Engine {
  start(): Promise<import('../engine').EngineState>;
  tick(): Promise<import('../engine').EngineState>;
  stop(): void;
  status(): import('../engine').EngineState;
}
