export interface PlayerState {
  id: string;
  x: number;
  y: number;
  health: number;
}

export interface LevelState {
  id: string;
  name: string;
  tiles: number[][];
  players: Record<string, PlayerState>;
}

export class InMemoryStore {
  public levels: Map<string, LevelState>;

  constructor() {
    this.levels = new Map<string, LevelState>();
  }

  private ensureLevel(levelId: string, name?: string): LevelState {
    let level = this.levels.get(levelId);
    if (!level) {
      level = {
        id: levelId,
        name: name ?? `Level ${levelId}`,
        tiles: [[]],
        players: {},
      };
      this.levels.set(levelId, level);
    }
    return level;
  }

  loadLevel(levelId: string, data: { name?: string; tiles?: number[][]; players?: Record<string, PlayerState> }): LevelState {
    const level = this.ensureLevel(levelId, data.name);
    if (data.tiles) {
      level.tiles = data.tiles;
    }
    if (data.players) {
      level.players = data.players;
    }
    return level;
  }

  saveLevel(levelId: string): LevelState {
    const level = this.levels.get(levelId);
    if (!level) {
      throw new Error(`Level ${levelId} not found`);
    }
    return level;
  }

  addOrUpdatePlayer(levelId: string, p: PlayerState): void {
    const level = this.ensureLevel(levelId);
    level.players[p.id] = p;
  }

  movePlayer(levelId: string, playerId: string, x: number, y: number): { ok: boolean; reason?: string } {
    const level = this.levels.get(levelId);
    if (!level) {
      return { ok: false, reason: 'Level not found' };
    }
    let player = level.players[playerId];
    if (!player) {
      // create player if missing
      player = { id: playerId, x, y, health: 100 };
      level.players[playerId] = player;
    } else {
      player.x = x;
      player.y = y;
    }
    return { ok: true };
  }

  shoot(levelId: string, shooterId: string, targetX: number, targetY: number): { hit: boolean; targetId?: string; damage?: number } {
    const level = this.levels.get(levelId);
    if (!level) return { hit: false };
    const shooter = level.players[shooterId];
    if (!shooter) return { hit: false };

    // Find nearest other player within radius 5
    let target: PlayerState | null = null;
    let minDist = Infinity;
    for (const pid of Object.keys(level.players)) {
      if (pid === shooterId) continue;
      const pl = level.players[pid];
      const dx = pl.x - shooter.x;
      const dy = pl.y - shooter.y;
      const dist = Math.hypot(dx, dy);
      if (dist <= 5 && dist < minDist) {
        minDist = dist;
        target = pl;
      }
    }
    if (!target) return { hit: false };

    // Apply damage
    target.health = Math.max(0, target.health - 10);
    return { hit: true, targetId: target.id, damage: 10 };
  }
}

export function createEmptyStore(): InMemoryStore {
  return new InMemoryStore();
}
