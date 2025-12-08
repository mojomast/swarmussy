import { describe, it, expect } from 'vitest';
import { World } from '../world';
import type { WorldECS } from '../ecs';

describe('World integration with ECS (gravity-like tick)', () => {
  it('updates position based on velocity when stepping', () => {
    // Build a minimal in-memory ECS compatible object
    const ecs = {
      positions: new Map<number, { x: number; y: number }>(),
      velocities: new Map<number, { x: number; y: number }>(),
      sizes: new Map<number, { w: number; h: number }>(),
      removeAll(): void {},
    } as unknown as WorldECS

    // Seed an entity
    ecs.positions.set(1, { x: 0, y: 0 })
    ecs.velocities.set(1, { x: 2, y: 3 })

    const world = new World(ecs as WorldECS)

    world.step(1)

    const pos = ecs.positions.get(1)
    expect(pos).toBeDefined()
    expect(pos!.x).toBe(2)
    expect(pos!.y).toBe(3)
  })

  it('supports stepping with non-unit dt', () => {
    const ecs = {
      positions: new Map<number, { x: number; y: number }>(),
      velocities: new Map<number, { x: number; y: number }>(),
      sizes: new Map<number, { w: number; h: number }>(),
      removeAll(): void {},
    } as unknown as WorldECS

    ecs.positions.set(2, { x: 0, y: 0 })
    ecs.velocities.set(2, { x: 1, y: 0.5 })

    const world = new World(ecs as WorldECS)
    world.step(2) // dt = 2
    const pos = ecs.positions.get(2)
    expect(pos).toBeDefined()
    expect(pos!.x).toBe(2)
    expect(pos!.y).toBe(1)
  })
})
