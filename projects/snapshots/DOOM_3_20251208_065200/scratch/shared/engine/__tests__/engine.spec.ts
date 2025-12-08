import { EngineImpl } from '../engine_impl';
import { createStore } from '../../server';
import type { InMemoryStore } from '../../server';

describe('EngineImpl - gravity-like tick on in-memory world', () => {
  let store: InMemoryStore;
  let engine: EngineImpl;
  const levelId = 'level-1';
  const playerId = 'player-1';

  beforeEach(() => {
    // fresh store per test
    store = createStore();
    // initialize one level with a single player at y=0
    const grid = Array.from({ length: 8 }, () => Array.from({ length: 8 }, () => ' '));
    store.levels[levelId] = {
      id: levelId,
      name: 'Level 1',
      width: 8,
      height: 8,
      tiles: grid,
      players: {},
    } as any;
    (store.levels[levelId]!.players as any)[playerId] = {
      id: playerId,
      x: 0,
      y: 0,
      hp: 100,
      facing: 'down',
    };
    engine = new EngineImpl(store);
  });

  it('start initializes and tick increments tick and updates y by gravity*dt', async () => {
    await engine.start();
    const s1 = await engine.tick(16);
    expect(s1.tick).toBe(1);
    const p = store.levels[levelId].players![playerId] as any;
    const expected = 9.81 * (16 / 1000);
    expect(p.y).toBeCloseTo(expected, 3);
  });

  it('tick with large dt clamps y to level floor', async () => {
    await engine.start();
    await engine.tick(16);
    // now apply a large delta to force clamp
    const s2 = await engine.tick(1000);
    // clamp to level height - 1 which is 7
    const p = store.levels[levelId].players![playerId] as any;
    expect(p.y).toBeCloseTo(7, 3);
    expect(s2.tick).toBe(2);
  });

  it('step() advances world and increments tick', () => {
    // ensure step can be called after start
    return engine.start().then(() => {
      const s = engine.step(16);
      expect(s.tick).toBeGreaterThanOrEqual(1);
      // next tick should increment again when tick() is called
    });
  });

  it('getWorldState exposes a snapshot view and is not the live store', () => {
    engine.start();
    const ws1 = engine.getWorldState();
    ws1.entities.set('spoof', { id: 'spoof' } as any);
    const ws2 = engine.getWorldState();
    expect(ws2.entities.has('spoof')).toBe(false);
  });
});
