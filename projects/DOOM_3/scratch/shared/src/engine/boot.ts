import type { World, Entity } from './ecs';
import { Position, Velocity, Renderable } from './components';
import { createPlayer } from './player';
import { System } from './system';

// Initialize a minimal world with a player and a couple of test entities
export function initWorld(): { world: World; player: Entity } {
  const world = new World();
  const player = createPlayer(world, 'Player');
  // Optional: add a second entity to demonstrate multi-entity updates
  const s = world.createEntity();
  world.addComponent(s, Position(5, 5));
  world.addComponent(s, Velocity(0.2, 0.1));
  world.addComponent(s, Renderable('#', '#0f0'));

  return { world, player };
}

// Movement system: updates Position by Velocity per frame
const movementSystem = new System('Movement', (dt: number, world: World) => {
  const entities = world.getEntitiesWithComponent('Position');
  for (const e of entities) {
    const pos = world.getComponent<any>(e, 'Position');
    const vel = world.getComponent<any>(e, 'Velocity');
    if (pos && vel) {
      pos.x += vel.x * dt;
      pos.y += vel.y * dt;
    }
  }
});

// Simple game loop runner with start/stop control
export function startGameLoop(world: World, systems: System[] = [movementSystem]): { stop: () => void } {
  let running = true;
  let last = (typeof performance !== 'undefined' && performance.now()) || Date.now();

  function frame(now: number) {
    if (!running) return;
    const dt = Math.min(0.032, (now - last) / 1000);
    last = now;
    for (const s of systems) {
      s.run(dt, world);
    }
    if (typeof window !== 'undefined' && (window as any).requestAnimationFrame) {
      (window as any).requestAnimationFrame(frame);
    } else {
      // Fallback in non-browser environments
      setTimeout(() => frame(performance?.now?.() ?? Date.now()), 16);
    }
  }

  if (typeof window !== 'undefined' && (window as any).requestAnimationFrame) {
    (window as any).requestAnimationFrame(frame);
  } else {
    frame(Date.now());
  }

  return {
    stop: () => {
      running = false;
    },
  };
}

// Re-export helpers for convenience
export { movementSystem };
