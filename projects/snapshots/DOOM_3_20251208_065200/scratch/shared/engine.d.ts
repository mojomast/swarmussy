export interface World {
  // minimal world container surface for engine integration
  levels: Record<string, any>;
}
export interface WorldView {
  levels: Record<string, any>;
}
export interface WorldUpdate {
  levels?: Record<string, any>;
}
export interface Entity {
  id: string;
  // minimal
  x?: number;
  y?: number;
}
export interface EngineLike {
  start(): void;
  stop(): void;
  tick(deltaMs: number): void;
}
