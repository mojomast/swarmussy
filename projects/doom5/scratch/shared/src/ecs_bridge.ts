// Tiny ECS World Bridge (Frontend)
// Provides a minimal API to interact with a simulated ECS World.

export type WorldState = {
  grid: number[][];
  entities: { id: string; x: number; y: number; w?: number; h?: number; color?: string }[];
};

type UpdateCallback = (state: WorldState) => void;

class ECSBridge {
  private static instance: ECSBridge;
  private state: WorldState;
  private listeners: UpdateCallback[] = [];

  private constructor() {
    const size = 10;
    this.state = {
      grid: Array.from({ length: size }, () => Array.from({ length: size }, () => 0)),
      entities: [],
    };
  }

  static getInstance(): ECSBridge {
    if (!ECSBridge.instance) ECSBridge.instance = new ECSBridge();
    return ECSBridge.instance;
  }

  connect() {
    // No-op for this lightweight bridge
  }

  getState(): WorldState {
    return this.state;
  }

  setTile(x: number, y: number, value: 0 | 1) {
    if (y >= 0 && y < this.state.grid.length && x >= 0 && x < this.state.grid[0].length) {
      this.state.grid[y][x] = value;
      this.emit();
    }
  }

  setWall(x: number, y: number) {
    this.setTile(x, y, 1);
  }

  clearTile(x: number, y: number) {
    this.setTile(x, y, 0);
  }

  onUpdate(cb: UpdateCallback) {
    this.listeners.push(cb);
    // Return unsubscribe function
    return () => {
      this.listeners = this.listeners.filter((l) => l !== cb);
    };
  }

  private emit() {
    for (const cb of this.listeners) {
      cb(this.state);
    }
  }
}

export function getWorldBridge(): ECSBridge {
  return ECSBridge.getInstance();
}

export type { WorldState };
