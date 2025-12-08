// Lightweight ECS testing helpers
import { World } from './world';
import type { Entity } from './ecs';

// Create a fresh world for tests
export function createTestWorld(): World {
  return new World();
}

// Add a simple entity with position and velocity components
export function addTestEntity(world: World): Entity {
  const e = world.createEntity();
  world.addComponent(e, 'position', { x: 0, y: 0 });
  world.addComponent(e, 'velocity', { x: 1, y: 0 });
  return e;
}

// Run a single tick with a simple inline MovementSystem
export function runSingleTick(world: World, dt: number = 0.016): void {
  const movementSystem = {
    execute(w: World, delta: number) {
      for (const [entity, compMap] of w.entities) {
        const pos = compMap.get('position');
        const vel = compMap.get('velocity');
        if (pos && vel) {
          pos.x += vel.x * delta;
          pos.y += vel.y * delta;
        }
      }
    }
  } as any;
  world.addSystem(movementSystem);
  world.tick(dt);
}

// Helper to get a position component by entity
export function getPosition(world: World, entity: Entity): { x: number; y: number } | undefined {
  const pos = world.getComponent<{ x: number; y: number }>(entity, 'position');
  return pos;
}
