import World from '../src/engine/world.js';

test('ecs basic create, components, and tick', () => {
  const world = new World();
  const e = world.createEntity();
  world.addComponent(e, 'position', { x: 0, y: 0 });
  world.addComponent(e, 'velocity', { x: 2, y: 0 });

  // Define a simple system that moves the entity this tick
  const sys = {
    execute(w, dt) {
      const pos = w.getComponent(e, 'position');
      const vel = w.getComponent(e, 'velocity');
      if (pos && vel) {
        pos.x += vel.x * dt;
        pos.y += vel.y * dt;
      }
    }
  };

  world.addSystem(sys);
  world.tick(0.5);

  const pos = world.getComponent(e, 'position');
  expect(pos.x).toBeCloseTo(1.0);
  expect(pos.y).toBeCloseTo(0.0);
});
