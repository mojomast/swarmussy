import type { World } from './ecs';
import type { Entity } from './ecs';
import { Position, Velocity, Renderable } from './components';

// Creates a simple Player entity with Position, Velocity, and Renderable components
export function createPlayer(world: World, name: string = 'Player'): Entity {
  const id = world.createEntity();
  // Initial player state
  world.addComponent(id, Position(0, 0));
  world.addComponent(id, Velocity(0, 0));
  world.addComponent(id, Renderable('@', '#fff'));
  // Could also register player with a UI, name association, etc.
  return id;
}
