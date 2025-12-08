// Simple renderer wrapper around Canvas 2D

import { Position, Sprite, World } from './ecs';

export class CanvasRenderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas2D not supported');
    this.ctx = ctx;
  }
  getContext(): CanvasRenderingContext2D {
    return this.ctx;
  }
  resizeToWindow() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  }
  clear() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }
  drawPositionedSprite(pos: Position, sprite: Sprite) {
    this.ctx.fillStyle = sprite.color;
    this.ctx.fillRect(pos.x, pos.y, sprite.w, sprite.h);
  }
}
