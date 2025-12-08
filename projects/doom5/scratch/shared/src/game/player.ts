// Player bootstrap and tiny demo loop

import { World, Position, Velocity, Sprite } from '../engine/ecs';
import { KeyboardInput, InputState } from '../engine/input';
import { CanvasRenderer } from '../engine/renderer';

export function createPlayer(world: World): number {
  const id = world.createEntity();
  world.addPosition(id, { x: 50, y: 50 });
  world.addVelocity(id, { vx: 0, vy: 0 });
  world.addSprite(id, { w: 20, h: 20, color: '#0f0' });
  return id;
}

export function bootstrapDemo(): void {
  // Create a tiny canvas in body
  const canvas = document.createElement('canvas');
  document.body.appendChild(canvas);
  const renderer = new CanvasRenderer(canvas);
  renderer.resizeToWindow();

  // World and player
  const world = new World();
  const player = createPlayer(world);

  // Input
  const input = new KeyboardInput();

  // Simple game loop using requestAnimationFrame
  let last = performance.now();
  function tick(now: number) {
    const dt = Math.min(0.05, (now - last) / 1000); // clamp dt
    last = now;

    // Input -> velocity
    const state: InputState = input.getState();
    const vel = world.velocities.get(player)!;
    const speed = 120; // px per second
    vel.vx = (state.right ? speed : 0) - (state.left ? speed : 0);
    vel.vy = (state.down ? speed : 0) - (state.up ? speed : 0);

    // Physics: integrate position
    const pos = world.positions.get(player)!;
    pos.x += vel.vx * dt;
    pos.y += vel.vy * dt;

    // Render
    renderer.clear();
    const sprite = world.sprites.get(player)!;
    renderer.drawPositionedSprite(pos, sprite);

    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
