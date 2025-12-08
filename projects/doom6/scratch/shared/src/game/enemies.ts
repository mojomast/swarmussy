// Basic enemy components and simple AI
import { Entity } from '../engine/core';
import { World } from '../engine/core';
import { Vec2 } from '../engine/core';
import { Position, EnemyMarker } from './components';

export class EnemyAIComponent {
  constructor(public entity: Entity) {}
  update(dt: number, world: World) {
    const pos = world.getComponent<Position>(this.entity, Position);
    if (!pos) return;
    // simple patrol
    const speed = pos.vx ?? 20;
    pos.x += speed * dt;
    // bounce
    if (pos.x > (pos.patrolMax ?? 300) || pos.x < (pos.patrolMin ?? 0)) pos.vx = -speed;
  }
}
