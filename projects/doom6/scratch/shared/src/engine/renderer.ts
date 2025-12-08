import { World, Vec2 } from './core';

export class CanvasStub {
  constructor(public width: number = 800, public height: number = 600) {}
  // fake canvas API
  getContext(_type: string) {
    return {
      fillRect: (_x: number, _y: number, _w: number, _h: number) => {},
      beginPath: () => {},
      moveTo: (_x: number, _y: number) => {},
      lineTo: (_x: number, _y: number) => {},
      stroke: () => {},
      strokeStyle: '#000',
    };
  }
}

export class Renderer {
  constructor(private canvas: CanvasStub) {}
  drawLine(x1: number, y1: number, x2: number, y2: number) {
    const ctx = this.canvas.getContext('2d');
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }
  drawRect(x: number, y: number, w: number, h: number) {
    const ctx = this.canvas.getContext('2d');
    ctx.fillRect(x, y, w, h);
  }
  // basic render loop hook
  render(dt: number) {
    // no-op for tests
  }
}
