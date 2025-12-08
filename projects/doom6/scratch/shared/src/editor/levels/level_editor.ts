// Level persistence editor: saveLevel(level) -> JSON, loadLevel(filename) -> LevelData,
// and export to a universal JSON schema

export interface LevelData {
  filename?: string;
  width: number;
  height: number;
  tiles: number[][];
  entities?: Array<{ id?: string; type: string; x: number; y: number }>;
  name?: string;
}

export class LevelEditor {
  // Simple in-memory storage for levels, acting as a stand-in for file I/O in this scaffold
  private static storage: Map<string, LevelData> = new Map<string, LevelData>();

  constructor() {}

  // Save a level to in-memory storage and return a pretty JSON payload
  saveLevel(level: LevelData): string {
    if (!level) throw new Error('Invalid level data');
    // Use filename as the storage key; if none, generate a unique one
    const key = level.filename ?? `level_${Date.now()}.json`;
    level.filename = key;
    LevelEditor.storage.set(key, level);
    return JSON.stringify(level, null, 2);
  }

  // Load a level by its filename from in-memory storage
  static loadLevel(filename: string): LevelData | undefined {
    return LevelEditor.storage.get(filename);
  }

  // Utility: export a level as a universal JSON schema (could be used by editors/UI)
  static toUniversalSchema(level: LevelData): any {
    // For this MVP, the schema is simply the LevelData structure
    return {
      filename: level.filename,
      width: level.width,
      height: level.height,
      tiles: level.tiles,
      entities: level.entities ?? [],
      name: level.name ?? level.filename,
    };
  }

  // Convenience: export to universal JSON string
  static exportFromLevel(level: LevelData): string {
    const schema = LevelEditor.toUniversalSchema(level);
    return JSON.stringify(schema, null, 2);
  }
}

export default LevelEditor;
