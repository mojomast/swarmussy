import { World, MovementSystem, Position, Velocity, Entity } from '../src/ecs';

describe('MovementSystem tests', () => {
  test('moves entity according to velocity and dt', () => {
    const world = new World();
    const e = new Entity();
    // Attach components
    world.addComponent(e, 'Position', new Position(0, 0));
    world.addComponent(e, 'Velocity', new Velocity(2, 3));
    // boot and tick
    world.registerSystem(new MovementSystem());
    world.tick(1);

    const pos = world.getComponent<Position>(e, 'Position');
    expect(pos).toBeDefined();
    expect(pos!.x).toBe(2);
    expect(pos!.y).toBe(3);
  });

  test('dt = 0 does not move entity', () => {
    const world = new World();
    const e = new Entity();
    world.addComponent(e, 'Position', new Position(5, 7));
    world.addComponent(e, 'Velocity', new Velocity(1, 1));
    world.registerSystem(new MovementSystem());
    world.tick(0);

    const pos = world.getComponent<Position>(e, 'Position');
    expect(pos).toBeDefined();
    expect(pos!.x).toBe(5);
    expect(pos!.y).toBe(7);
  });
});
