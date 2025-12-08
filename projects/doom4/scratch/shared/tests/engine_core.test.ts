import { World, Engine, Position, Velocity, Renderable, Camera, AI } from '../engine-core';

describe('ECS Core', () => {
  it('can create entity and add components', () => {
    const w = new World();
    const e = w.createEntity();
    w.addComponent<Position>(e, 'Position', { x: 1, y: 2, z: 0 });
    w.addComponent<Velocity>(e, 'Velocity', { x: 0, y: 0, z: 0 });
    expect(w.getComponent<Position>(e, 'Position')).toBeDefined();
    expect(w.getComponent<Velocity>(e, 'Velocity')).toBeDefined();
  });

  it('can query by components', () => {
    const w = new World();
    const e1 = w.createEntity();
    w.addComponent<Position>(e1, 'Position', { x: 0, y: 0, z: 0 });
    w.addComponent<Renderable>(e1, 'Renderable', { color: '#fff' });

    const e2 = w.createEntity();
    w.addComponent<Position>(e2, 'Position', { x: 1, y: 0, z: 0 });

    const res = w.getEntitiesWith('Position', 'Renderable');
    expect(res).toContain(e1);
    expect(res).not.toContain(e2);
  });

  it('can serialize/deserialize', () => {
    const w = new World();
    const e = w.createEntity();
    w.addComponent<Position>(e, 'Position', { x: 5, y: 6, z: 0 });
    const s = w.serialize();
    const w2 = new World();
    w2.deserialize(s);
    const pos = w2.getComponent<Position>(e, 'Position');
    // However, after deserialization, the entity IDs may not match; ensure a consistent round trip by re-creating mapping.
    expect(pos).toBeDefined();
  });

  it('can remove entities', () => {
    const w = new World();
    const e = w.createEntity();
    w.addComponent<Position>(e, 'Position', { x: 0, y: 0, z: 0 });
    w.removeEntity(e);
    const pos = w.getComponent<Position>(e, 'Position');
    expect(pos).toBeUndefined();
  });
});
