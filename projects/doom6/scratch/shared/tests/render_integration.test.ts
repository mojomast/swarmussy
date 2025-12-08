import { World, MovementSystem, Position, Velocity, Entity } from '../src/ecs';
import { CanvasStub, Renderer } from '../src/renderer';

describe('Rendering hooks integration', () => {
  test('Renderer can draw with canvas', () => {
    const world = new World();
    const e = new Entity();
    world.addComponent(e, 'Position', new Position(10, 20));
    world.registerSystem(new MovementSystem());
    world.tick(0.016);
    const canvas = new CanvasStub();
    const renderer = new Renderer(canvas);
    // render should not throw
    expect(() => {
      renderer.drawLine(0,0,10,10);
      renderer.drawRect(10,10,5,5);
    }).not.toThrow();
  });
});
