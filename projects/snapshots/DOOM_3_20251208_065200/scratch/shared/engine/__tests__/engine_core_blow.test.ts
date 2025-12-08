import { describe, it, expect } from 'vitest';
import { EngineImpl } from '../engine_impl';
import { createStore } from '../../server';
import type { InMemoryStore } from '../../server';

describe('EngineImpl blow test', () => {
  it('begins in stopped state', () => {
    const store = createStore();
    const e = new EngineImpl(store);
    const st = e.status();
    expect(st.running).toBe(false);
  });
});
