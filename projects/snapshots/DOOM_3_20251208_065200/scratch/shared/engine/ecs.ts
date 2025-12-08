export type Entity = number

export interface Component {}

export interface Position { x: number; y: number }
export interface Velocity { x: number; y: number }
export interface Size { w: number; h: number }

export interface WorldECS {
  positions: Map<Entity, Position>
  velocities: Map<Entity, Velocity>
  sizes: Map<Entity, Size>
  removeAll(): void
}
