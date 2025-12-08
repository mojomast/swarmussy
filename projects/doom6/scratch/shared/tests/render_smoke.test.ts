import { CanvasStub, Renderer } from '../src/render';

describe('Render smoke test', () => {
  test('draw calls execute without error', () => {
    const canvas = new CanvasStub(640, 480);
    const renderer = new Renderer(canvas);

    expect(() => {
      renderer.drawLine(0,0,10,10);
      renderer.drawRect(5,5,20,20);
    }).not.toThrow();
  });
});
