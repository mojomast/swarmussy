// Engine API facade for world interaction
import type { ECS, Entity, Position, Velocity, Size } from './ecs';
import type { World } from './world';

export interface WorldState {
  entities: Entity[];
  positions: Record<string, Position>;
  velocities: Record<string, Velocity>;
  sizes: Record<string, Size>;
}

export class EngineAPI {
  private world: World;
  constructor(world?: World) {
    this.world = world ?? new World();
  }

  async getWorldState(): Promise<WorldState> {
    return this.world.getState();
  }

  async step(dt: number = 1): Promise<void> {
    this.world.step(dt);
  }

  async reset(): Promise<void> {
    this.world.reset();
  }
}
