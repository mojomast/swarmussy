import { World, Position, Velocity, Sprite } from '../src/engine/ecs';

describe('World ECS basics', () => {
  test('create entity and attach components', () => {
    const world = new World();
    const e = world.createEntity();
    world.addPosition(e, { x: 5, y: 7 });
    world.addVelocity(e, { vx: 1, vy: -1 });
    world.addSprite(e, { w: 10, h: 10, color: '#fff' });
    expect(world.positions.get(e)).toEqual({ x: 5, y: 7 });
    expect(world.velocities.get(e)).toEqual({ vx: 1, vy: -1 });
    expect(world.sprites.get(e)).toEqual({ w: 10, h: 10, color: '#fff' });
  });
});
