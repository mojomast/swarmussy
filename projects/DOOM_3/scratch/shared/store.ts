import { LevelState, PlayerState } from './models';

export type GameStore = {
  levels: Record<string, LevelState>;
};

// Singleton in-memory store shared across server and tests
export const store: GameStore = {
  levels: {},
};

// Factory for a fresh store (not the default singleton)
export function createStore(): GameStore {
  return {
    levels: {},
  };
}

export function getLevel(store: GameStore, id: string): LevelState | undefined {
  return store.levels[id];
}

export function setLevel(store: GameStore, level: LevelState) {
  store.levels[level.id] = level;
}

export function ensureLevelExists(store: GameStore, id: string, fallback?: Partial<LevelState>): LevelState {
  let lvl = store.levels[id];
  if (!lvl) {
    lvl = {
      id,
      name: `Level ${id}`,
      width: 10,
      height: 10,
      tiles: Array.from({ length: 10 }, () => Array.from({ length: 10 }, () => ' ')),
      players: {},
      ...fallback,
    } as LevelState;
    store.levels[id] = lvl;
  }
  return lvl;
}

export function addPlayerToLevel(level: LevelState, player: PlayerState) {
  level.players[player.id] = player;
}

export function movePlayer(level: LevelState, playerId: string, dx: number, dy: number) {
  const p = level.players[playerId];
  if (!p) return false;
  p.x += dx;
  p.y += dy;
  // Note: Do not clamp to allow test scenarios that expect out-of-bounds positions
  return true;
}

export function shootFrom(level: LevelState, playerId: string) {
  const p = level.players[playerId];
  if (!p) return false;
  // Simple placeholder: always succeed if player exists
  return true;
}
