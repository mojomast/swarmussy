import EngineCore from '../engine/core';
import type { LevelState } from '../models';

// Integration test: engine tick correctness across multiple levels with backend world

describe('Integration: EngineCore with backend world (levels/players)', () => {
  test('tick applies gravity to all players across levels deterministically', async () => {
    // Level 1 with one player starting at y=0
    const lvl1: LevelState = {
      id: 'lvl1',
      name: 'Level 1',
      width: 10,
      height: 10,
      tiles: Array.from({ length: 10 }, () => Array.from({ length: 10 }, () => ' ')),
      players: {
        'p1': { id: 'p1', x: 0, y: 0, hp: 100, facing: 'down' },
      },
    };

    // Level 2 with another player
    const lvl2: LevelState = {
      id: 'lvl2',
      name: 'Level 2',
      width: 12,
      height: 12,
      tiles: Array.from({ length: 12 }, () => Array.from({ length: 12 }, () => ' ')),
      players: {
        'p2': { id: 'p2', x: 1, y: 2, hp: 100, facing: 'down' },
      },
    };

    const levels = { 'lvl1': lvl1, 'lvl2': lvl2 } as const;

    const engine = new EngineCore({ levels: (levels as any).levels ?? levels });

    // Start engine
    const startState = await engine.start();
    expect(startState.running).toBe(true);

    // Tick three times and capture intermediate states
    const snapshots: { lvl1: { p1: { y: number } }; lvl2: { p2: { y: number } } }[] = [];

    for (let i = 0; i < 3; i++) {
      await engine.tick();
      snapshots.push({
        lvl1: { p1: { y: lvl1.players['p1'].y } },
        lvl2: { p2: { y: lvl2.players['p2'].y } },
      });
    }

    // After 3 ticks, p1.y should be 3 (0 + 1*3) and p2.y should be 5 (2 + 1*3)
    expect(lvl1.players['p1'].y).toBe(3);
    expect(lvl2.players['p2'].y).toBe(5);

    // Validate the incremental snapshots reflect gravity progression
    expect(snapshots[0].lvl1.p1.y).toBe(1);
    expect(snapshots[0].lvl2.p2.y).toBe(3);
    expect(snapshots[1].lvl1.p1.y).toBe(2);
    expect(snapshots[1].lvl2.p2.y).toBe(4);
    expect(snapshots[2].lvl1.p1.y).toBe(3);
    expect(snapshots[2].lvl2.p2.y).toBe(5);

    engine.stop();
  });
});
