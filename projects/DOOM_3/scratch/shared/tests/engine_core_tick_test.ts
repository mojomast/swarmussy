import { EngineCore } from '../engine/core/core_engine';
import type { LevelState, PlayerState } from '../models';

describe('EngineCore tick plan', () => {
  test('gravity tick increments y', () => {
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
    engine.start();
    engine.tick();

    const p = world.levels['lvl1'].players['p1'];
    expect(p.y).toBeGreaterThan(0);
  });
});
