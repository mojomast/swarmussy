import { describe, test, expect } from 'vitest';
import { EngineAPIImpl } from '../engine_api';
import { World } from '../world';

// Test frontend fetch wrappers used by UI to talk to the engine API

describe('Integration: Engine fetch wrappers', () => {
  test('getWorldState outputs', () => {
    const w = new World();
    const api = new EngineAPIImpl(w);
    const s = api.getWorldState();
    expect(s).toBeDefined();
  });
});
