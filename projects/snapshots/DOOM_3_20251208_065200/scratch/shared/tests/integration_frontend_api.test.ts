import { describe, test, expect } from 'vitest';
import { EngineAPIImpl } from '../engine_api';
import { World } from '../world';

describe('Frontend Engine API', () => {
  test('getWorldState returns defined', () => {
    const w = new World();
    const api = new EngineAPIImpl(w);
    const s = api.getWorldState();
    expect(s).toBeDefined();
  });
});
