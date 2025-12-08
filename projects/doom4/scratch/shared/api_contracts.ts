// API contracts for editor state, plans, assets, levels, and world persistence

export type EditorMode = 'edit' | 'play';

export interface EditorState {
  editorId: string;
  mode: EditorMode;
  activePlanId?: string;
  activeLevelId?: string;
  lastModified: string;
}

export interface PlanState {
  planId: string;
  name: string;
  description?: string;
  status: 'draft' | 'review' | 'ready';
  updatedAt: string;
}

export type AssetType = 'monster' | 'weapon' | 'texture' | 'sound' | 'asset';

export interface AssetMeta {
  assetId: string;
  type: AssetType;
  name: string;
  metadata?: any;
  updatedAt: string;
}

export interface LevelMeta {
  levelId: string;
  name: string;
  width: number;
  height: number;
  updatedAt: string;
}

export interface WorldState {
  worldId: string;
  editor: EditorState;
  plan: PlanState;
  assets: AssetMeta[];
  levels: LevelMeta[];
  map?: any;
  createdAt: string;
  updatedAt: string;
}

// Generic API response wrapper
export interface ApiResponse<T> {
  ok: boolean;
  data?: T;
  error?: string;
}

// Payload shapes for updates
export interface EditorStatePayload {
  mode?: EditorMode;
  activePlanId?: string;
  activeLevelId?: string;
}

export interface PlanStatePayload {
  name?: string;
  description?: string;
  status?: PlanState['status'];
}

export interface AssetMetaPayload {
  assetId?: string; // if provided, update existing; otherwise create new
  type?: AssetType;
  name?: string;
  metadata?: any;
}

export interface LevelMetaPayload {
  levelId?: string;
  name?: string;
  width?: number;
  height?: number;
}

export type WorldPayload = Partial<WorldState>;
