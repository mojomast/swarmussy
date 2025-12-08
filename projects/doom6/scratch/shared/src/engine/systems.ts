// ECS Systems: Movement, AI, Shooting
import { World, Vec2, Entity, System } from './core';
import { Position, PlayerMarker, EnemyMarker } from '../game/components';
import { Input } from './input';

// Movement system for player controlled by input
export class MovementSystem implements System {
  constructor(private input: Input) {}
  update(dt: number, world: World): void {
    const players = world.getEntitiesWithComponents([Position, PlayerMarker]);
    const dx = (this.input.state.right ? 1 : 0) - (this.input.state.left ? 1 : 0);
    const dy = (this.input.state.down ? 1 : 0) - (this.input.state.up ? 1 : 0);
    const speed = 120; // units per second
    for (const e of players) {
      const p = world.getComponent<Position>(e, Position);
      if (!p) continue;
      const vx = dx * speed * dt;
      const vy = dy * speed * dt;
      p.x += vx;
      p.y += vy;
    }
  }
}

// Basic enemy AI: patrol and slight aggro towards player
export class EnemySystem implements System {
  update(dt: number, world: World): void {
    const enemies = world.getEntitiesWithComponents([Position, EnemyMarker]);
    const players = world.getEntitiesWithComponents([Position, PlayerMarker]);
    const playerPos = players.length > 0 ? world.getComponent<Position>(players[0], Position) : undefined;
    for (const e of enemies) {
      const pos = world.getComponent<Position>(e, Position);
      if (!pos) continue;
      // Patrol default velocity
      if (pos.vx == null) pos.vx = 40;
      // Aggro if player nearby
      if (playerPos) {
        const dist = Math.hypot(playerPos.x - pos.x, playerPos.y - pos.y);
        if (dist < 150) {
          // chase
          const dirx = (playerPos.x - pos.x) / (dist || 1);
          const diry = (playerPos.y - pos.y) / (dist || 1);
          pos.x += dirx * (60 * dt);
          pos.y += diry * (60 * dt);
          continue;
        }
      }
      // Patrol movement along X axis
      pos.x += (pos.vx ?? 40) * dt;
      if (pos.patrolMin != null && pos.x < pos.patrolMin) pos.vx = Math.abs(pos.vx ?? 40);
      if (pos.patrolMax != null && pos.x > pos.patrolMax) pos.vx = -Math.abs(pos.vx ?? 40);
    }
  }
}

// Shooting system: perform raycast from player and remove hit enemy if any
export class ShootingSystem implements System {
  constructor(private input: Input) {}
  update(dt: number, world: World): void {
    if (!this.input.state.shoot) return;
    const players = world.getEntitiesWithComponents([Position, PlayerMarker]);
    if (players.length === 0) return;
    const playerPos = world.getComponent<Position>(players[0], Position);
    if (!playerPos) return;
    // Shoot along +X axis for simplicity
    const origin = new Vec2(playerPos.x, playerPos.y);
    const dir = new Vec2(1, 0);
    const hit = world.raycast(origin, dir, 1000, [EnemyMarker]);
    if (hit) {
      // Remove hit enemy
      world.removeEntity(hit.entity);
      // Reset shoot flag to prevent rapid consecutive kills in a single frame
      this.input.state.shoot = false;
      console.log('Hit enemy', hit.entity);
    }
  }
}
