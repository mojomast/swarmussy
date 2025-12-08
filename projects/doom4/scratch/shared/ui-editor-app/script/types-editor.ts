// UI-facing editor entity typings
export interface EditorState {
  editorId: string;
  mode: 'edit' | 'play';
  activePlanId?: string;
  activeLevelId?: string;
  lastModified?: string;
}

export interface LevelMeta {
  levelId: string;
  name: string;
  width: number;
  height: number;
  updatedAt?: string;
}

export interface AssetMeta {
  assetId: string;
  type: string;
  name: string;
  metadata?: any;
  updatedAt?: string;
}

export interface EntityMeta {
  id: string;
  type: string;
  name?: string;
  levelId?: string;
  components?: any;
  updatedAt?: string;
}

export interface Monster {
  id: string;
  name: string;
  hp: number;
}

export interface Weapon {
  id: string;
  name: string;
  damage: number;
}
