export type LevelData = {
  id?: string
  name: string
  width: number
  height: number
  grid?: number[][]
}

export type LevelStore = Record<string, LevelData>

export function createDefaultLevels(): LevelStore {
  return {
    'level-1': { id: 'level-1', name: 'Level 1', width: 16, height: 12, grid: [] },
  }
}
