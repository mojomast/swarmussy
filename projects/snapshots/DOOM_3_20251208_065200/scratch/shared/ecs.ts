export type Entity = number;

export interface Position {
  x: number;
  y: number;
}

export interface Velocity {
  x: number;
  y: number;
}

export interface Size {
  w: number;
  h: number;
}

// Minimal runtime ECS container interface
export interface WorldECS {
  positions: Map<Entity, Position>;
  velocities: Map<Entity, Velocity>;
  sizes: Map<Entity, Size>;
  removeAll(): void;
}

// Simple concrete ECS implementation
export class SimpleWorldECS implements WorldECS {
  positions: Map<Entity, Position> = new Map();
  velocities: Map<Entity, Velocity> = new Map();
  sizes: Map<Entity, Size> = new Map();

  removeAll(): void {
    this.positions.clear();
    this.velocities.clear();
    this.sizes.clear();
  }
}
