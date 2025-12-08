import type { Position, Velocity, Renderable, Health } from './components';
import type { Entity } from '../engine/ecs';

export class EntityBuilder {
  private components: Map<string, any> = new Map();
  constructor(private world: any) {}
  with<T>(key: string, comp: T): this {
    this.components.set(key, comp);
    return this;
  }
  build(): Entity {
    const e = this.world.createEntity();
    for (const [k, v] of this.components) {
      this.world.addComponent(e, k, v);
    }
    return e as unknown as Entity;
  }
}

export function createPlayer(world: any, x: number, y: number): number {
  const builder = new EntityBuilder(world);
  return builder.with<Position>('position', { x, y, z: 0 })
    .with<Velocity>('velocity', { x: 0, y: 0, z: 0 })
    .with<Renderable>('renderable', { sprite: 'player', color: '#00f' })
    .build();
}
