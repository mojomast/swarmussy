// Player component and movement logic
import { World } from '../engine/core';
import { Position } from './components';
export class PlayerController {
  constructor(public entity: number) {}
  update(dt: number, world: World, input: { up: boolean, down: boolean, left: boolean, right: boolean, mouseX?: number, mouseY?: number }) {
    const pos = world.getComponent<Position>(this.entity, Position);
    if (!pos) return;
    const speed = 80;
    const dx = (input.right ? 1 : 0) - (input.left ? 1 : 0);
    const dy = (input.down ? 1 : 0) - (input.up ? 1 : 0);
    pos.x += dx * speed * dt;
    pos.y += dy * speed * dt;
  }
}
