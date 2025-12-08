import { describe, it, expect } from 'vitest';
import { World } from '../world';
import { EngineAPIImpl } from '../engine_api';

// Core API tests for in-memory world layer

describe('Core API (World) basics', () => {
  it('creates world, adds player, and steps', () => {
    const w = new World();
    const playerId = 'p1';
    // expect world to have API surface; this is a light smoke test
    w.createPlayer(0, 0);
    w.createWall(1, 1, 2, 2);
    w.step(1);
    const state = w.getState();
    expect(state.entities.length).toBeGreaterThanOrEqual(1);
  });
});
