import EngineCore from '../engine/core';
import type { LevelState, PlayerState } from '../models';

describe('EngineCore (in-memory world) skeleton', () => {
  test('start/stop/tick basic flow', async () => {
    // prepare a small in-memory world with one level and one player
    const lvl: LevelState = {
      id: 'lvl1',
      name: 'Level 1',
      width: 10,
      height: 10,
      tiles: Array.from({ length: 10 }, () => Array.from({ length: 10 }, () => ' ')),
      players: {
        'p1': { id: 'p1', x: 0, y: 0, hp: 100, facing: 'down' }
      },
    };

    const testStore = { levels: { 'lvl1': lvl } } as { levels: Record<string, LevelState> };

    const engine = new EngineCore({ levels: testStore.levels });

    // start
    const startState = await engine.start();
    expect(startState.running).toBe(true);

    // one tick should apply gravity to player y (y increases by 1 per tick)
    const beforeY = lvl.players['p1'].y;
    await engine.tick();
    const afterY = lvl.players['p1'].y;
    expect(afterY).toBeGreaterThan(beforeY);

    // stop
    engine.stop();
    const status = engine.status();
    expect(status.running).toBe(false);
  });
});
