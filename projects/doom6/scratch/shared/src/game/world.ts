import { ECS } from './ecs';
import { World as EditorWorld } from '../editor/engine/core';

// Simple compatibility shim for tests and runtime
export class World {
  private ecs = new ECS();

  createEntity(): number {
    return this.ecs.createEntity();
  }

  addComponent(entity: number, component: any): void {
    this.ecs.addComponent(entity, component);
  }
}

export default World;
