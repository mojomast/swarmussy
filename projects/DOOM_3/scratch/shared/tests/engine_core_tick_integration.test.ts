import EngineCore from '../engine/core/core_engine';
import type { LevelState } from '../models';

describe('EngineCore (in backend world integration) skeleton', () => {
  test('start/stop/tick gravity updates player y across a single level', () => {
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

    const world = { levels: { 'lvl1': lvl } } as { levels: Record<string, LevelState> };

    const engine = new EngineCore(world);

    // start
    engine.start();

    // gravity tick
    const beforeY = lvl.players['p1'].y;
    engine.tick();
    const afterY = lvl.players['p1'].y;
    expect(afterY).toBeGreaterThan(beforeY);

    // stop
    engine.stop();
  });
});
