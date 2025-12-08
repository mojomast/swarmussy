// TypeScript API contracts and fetch-based client for frontend editor

// Interfaces (matching backend API contracts)
export interface EditorState {
  editorId: string;
  mode: 'edit' | 'play';
  activePlanId?: string;
  activeLevelId?: string;
  lastModified?: string;
}

export interface PlanState {
  planId: string;
  name: string;
  description?: string;
  status: 'draft' | 'review' | 'ready';
  updatedAt?: string;
}

export interface AssetMeta {
  assetId: string;
  type: string;
  name: string;
  metadata?: any;
  updatedAt?: string;
}

export interface LevelMeta {
  levelId: string;
  name: string;
  width: number;
  height: number;
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

// Payload shapes (optional, for updates)
export interface EditorStatePayload {
  mode?: EditorState['mode'];
  activePlanId?: string;
  activeLevelId?: string;
}

export interface PlanStatePayload {
  name?: string;
  description?: string;
  status?: PlanState['status'];
}

export interface AssetMetaPayload {
  assetId?: string;
  type?: string;
  name?: string;
  metadata?: any;
}

export interface LevelMetaPayload {
  levelId?: string;
  name?: string;
  width?: number;
  height?: number;
}

export class ApiClientFetch {
  static getEditorState(): Promise<EditorState> {
    return fetch('/api/editor/state', { method: 'GET', credentials: 'same-origin' })
      .then((r) => {
        if (!r.ok) throw new Error('Failed to fetch editor state');
        return r.json() as Promise<EditorState>;
      });
  }

  static getPlan(): Promise<PlanState> {
    return fetch('/api/editor/plan', { method: 'GET', credentials: 'same-origin' })
      .then((r) => {
        if (!r.ok) throw new Error('Failed to fetch plan');
        return r.json() as Promise<PlanState>;
      });
  }

  static getAssets(): Promise<AssetMeta[]> {
    return fetch('/api/editor/assets', { method: 'GET', credentials: 'same-origin' })
      .then((r) => {
        if (!r.ok) throw new Error('Failed to fetch assets');
        return r.json() as Promise<AssetMeta[]>;
      });
  }

  static getLevelsEntities(): Promise<{ levels: LevelMeta[]; entities: EntityMeta[] }> {
    return fetch('/api/editor/levels/entities', { method: 'GET', credentials: 'same-origin' })
      .then((r) => {
        if (!r.ok) throw new Error('Failed to fetch levels/entities');
        return r.json() as Promise<{ levels: LevelMeta[]; entities: EntityMeta[] }>;
      });
  }
}

export default ApiClientFetch;
