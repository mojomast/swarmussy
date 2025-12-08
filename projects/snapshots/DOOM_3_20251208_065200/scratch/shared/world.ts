import type { WorldECS, Entity, Position, Velocity, Size } from './ecs';

export interface WorldState {
  entities: Entity[];
  positions: Record<string, Position>;
  velocities: Record<string, Velocity>;
  sizes: Record<string, Size>;
}

export class World {
  ecs: WorldECS;

  constructor(ecs?: WorldECS) {
    this.ecs = ecs ?? new (require('./ecs').WorldECS)();
  }

  getState(): WorldState {
    const entities = Array.from(this.ecs.positions.keys())
      .concat(Array.from(this.ecs.velocities.keys()))
      .concat(Array.from(this.ecs.sizes.keys()))
      .filter((v, i, a) => a.indexOf(v) === i);

    const positions: Record<string, Position> = {};
    for (const [e, p] of this.ecs.positions) positions[e.toString()] = p;

    const velocities: Record<string, Velocity> = {};
    for (const [e, v] of this.ecs.velocities) velocities[e.toString()] = v;

    const sizes: Record<string, Size> = {};
    for (const [e, s] of this.ecs.sizes) sizes[e.toString()] = s;

    return { entities, positions, velocities, sizes };
  }

  step(dt: number = 1) {
    // naive step: update positions by velocity scaled by dt
    for (const [id, vel] of this.ecs.velocities) {
      const p = this.ecs.positions.get(id);
      if (p) {
        p.x += vel.x * dt;
        p.y += vel.y * dt;
      }
    }
  }

  reset(): void {
    this.ecs.removeAll();
  }
}
