import { World, ShootingSystem, Shooting, Position, Entity } from '../src/ecs';

describe('ShootingSystem tests', () => {
  test('spawns bullet when cooldown <= 0', () => {
    const world = new World();
    const e = new Entity();
    world.addComponent(e, 'Position', new Position(0, 0));
    world.addComponent(e, 'Shooting', new Shooting({ rate: 1, cooldown: 0, bulletSpeed: 1 }));
    world.registerSystem(new ShootingSystem());
    world.tick(1);
    // If we had a bullet, there should be an extra entity
    const count = world.getEntityCount();
    expect(count).toBeGreaterThan(1);
  });

  test('cooldown decreases over time', () => {
    const world = new World();
    const e = new Entity();
    world.addComponent(e, 'Position', new Position(0, 0));
    world.addComponent(e, 'Shooting', new Shooting({ rate: 2, cooldown: 0 }));
    world.registerSystem(new ShootingSystem());
    world.tick(0.5);
    const shoot = world.getComponent<any>(e, 'Shooting');
    expect(shoot).toBeDefined();
    expect(shoot.cooldown).toBeLessThanOrEqual(0.5);
  });
});
