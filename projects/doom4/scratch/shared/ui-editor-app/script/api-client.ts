// TypeScript API contracts and fetch-based client for frontend editor

export type EditorMode = 'edit' | 'play';

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

export interface WorldState {
  worldId: string;
  editor: EditorState;
  plan: PlanState;
  assets: AssetMeta[];
  levels: LevelMeta[];
  map?: any;
  createdAt?: string;
  updatedAt?: string;
}

function getAuthHeader(): { Authorization?: string } {
  try {
    const token = (typeof window !== 'undefined' && (window as any).localStorage.getItem('authToken')) || undefined;
    if (token) return { Authorization: 'Bearer ' + token };
  } catch (e) {
    // ignore
  }
  return {};
}

export default class ApiClient {
  private baseUrl: string;
  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  private async fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
    const headers: any = { 'Content-Type': 'application/json', ...getAuthHeader() };
    const resp = await fetch(path, { method: init?.method ?? 'GET', headers, ...init, credentials: 'same-origin' } as any);
    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error('Network error' + (errText ? ': ' + errText : ''));
    }
    return (await resp.json()) as T;
  }

  public static login(username: string, password: string): Promise<string> {
    // lightweight placeholder login, stores a demo token
    const token = 'demo-token';
    try {
      const w = (typeof window !== 'undefined') ? (window as any) : null;
      w?.localStorage.setItem('authToken', token);
    } catch {
      // ignore
    }
    return Promise.resolve(token);
  }

  public getEditorState(): Promise<EditorState> {
    return this.fetchJson<EditorState>(`${this.baseUrl}/api/editor/state`);
  }

  public getPlan(): Promise<PlanState> {
    return this.fetchJson<PlanState>(`${this.baseUrl}/api/editor/plan`);
  }

  public getAssets(): Promise<AssetMeta[]> {
    return this.fetchJson<AssetMeta[]>(`${this.baseUrl}/api/editor/assets`);
  }

  public getLevelsEntities(): Promise<{ levels: LevelMeta[]; entities: EntityMeta[] }> {
    return this.fetchJson<{ levels: LevelMeta[]; entities: EntityMeta[] }>(`${this.baseUrl}/api/editor/levels/entities`);
  }

  public updatePlan(plan: PlanState): Promise<PlanState> {
    return this.fetchJson<PlanState>(`${this.baseUrl}/api/editor/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(plan),
    } as any);
  }
}
