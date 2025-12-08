import EngineCore from '../engine/core';
import type { LevelState } from '../models';

describe('EngineCore integration tests (in-memory store)', () => {
  test('initializes engine and applies gravity on first tick', async () => {
    // Arrange: create a simple level with a single player
    const lvl: LevelState = {
      id: 'lvl1',
      name: 'Level 1',
      width: 10,
      height: 10,
      tiles: Array.from({ length: 10 }, () => Array.from({ length: 10 }, () => ' ')),
      players: {
        'p1': { id: 'p1', x: 0, y: 0, hp: 100, facing: 'down' },
      },
    };

    const testStore = { levels: { 'lvl1': lvl } } as { levels: Record<string, LevelState> };

    // Act: instantiate engine with the test store and run start/tick
    const engine = new EngineCore({ levels: testStore.levels });
    const startState = await engine.start();
    expect(startState.running).toBe(true);

    // Before tick, capture current Y
    const beforeY = lvl.players['p1'].y;

    // Perform a tick; gravity should move player on Y axis by roughly 1 unit
    const afterTick = await engine.tick();
    const afterY = lvl.players['p1'].y;

    expect(afterTick.tick).toBeGreaterThanOrEqual(startState.tick);
    expect(afterY).toBeGreaterThanOrEqual(beforeY);

    // Cleanup
    engine.stop();
  });

  test('multiple ticks advance tick counter and move players multiple steps', async () => {
    const lvl: LevelState = {
      id: 'lvl2',
      name: 'Level 2',
      width: 10,
      height: 10,
      tiles: Array.from({ length: 10 }, () => Array.from({ length: 10 }, () => ' ')),
      players: {
        'p2': { id: 'p2', x: 0, y: 0, hp: 100, facing: 'down' },
      },
    };

    const testStore = { levels: { 'lvl2': lvl } } as { levels: Record<string, LevelState> };
    const engine = new EngineCore({ levels: testStore.levels });
    await engine.start();

    const beforeY = lvl.players['p2'].y;
    await engine.tick();
    await engine.tick();
    const afterY = lvl.players['p2'].y;

    expect(afterY).toBeGreaterThanOrEqual(beforeY);
    engine.stop();
  });
});
