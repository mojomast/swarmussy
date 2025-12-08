import { describe, it, expect } from 'vitest';
import { World } from '../shared/world';
import { ECS } from '../shared/ecs';

describe('World basic', () => {
  it('can create entities and tick', () => {
    // Simple sanity test; World maintains in-memory ECS
    const w = new World();
    // no assertion; ensure code paths compile
    w.tick(0.016)
  });
});
