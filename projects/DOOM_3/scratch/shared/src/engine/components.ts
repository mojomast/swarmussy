import type { Entity } from './ecs';

export interface IPosition {
  x: number;
  y: number;
}

export interface IVelocity {
  x: number;
  y: number;
}

export interface IRenderable {
  char: string;
  color?: string;
}

// Marker component types
export const Position = (x: number, y: number) => ({ type: 'Position', x, y } as any);
export const Velocity = (x: number, y: number) => ({ type: 'Velocity', x, y } as any);
export const Renderable = (char: string, color?: string) => ({ type: 'Renderable', char, color } as any);
