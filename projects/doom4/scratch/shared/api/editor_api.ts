import fs from 'fs';
import path from 'path';

export type ID = string;

type PersistPath = string | undefined;

export interface Asset {
  id: ID;
  name: string;
  type?: string;
  data?: any;
  updatedAt?: string;
}

export interface Level {
  id: ID;
  name: string;
  description?: string;
  data?: any;
  updatedAt?: string;
}

export interface EntityMeta {
  id: ID;
  type: string;
  name?: string;
  levelId?: string;
  components?: any;
  updatedAt?: string;
}

export interface Plan {
  id: ID;
  name?: string;
  content?: any;
  updatedAt?: string;
}

export interface EditorState {
  assets: Asset[];
  levels: Level[];
  entities: EntityMeta[];
  plan?: Plan;
}

function nowIso(): string {
  return new Date().toISOString();
}

function ensureArray<T>(arr: T[] | undefined): T[] {
  return Array.isArray(arr) ? arr : [];
}

export class EditorStore {
  private assets: Asset[] = [];
  private levels: Level[] = [];
  private entities: EntityMeta[] = [];
  private plan?: Plan;
  private persistencePath?: string;
  private lastId: number = 1;

  constructor(persistPath?: string, seed?: Partial<EditorState>) {
    this.persistencePath = persistPath;
    if (persistPath) {
      this.loadFromDisk();
    }
    if (seed) {
      if (seed.assets) this.assets = seed.assets;
      if (seed.levels) this.levels = seed.levels;
      if (seed.entities) this.entities = seed.entities;
      if (seed.plan) this.plan = seed.plan;
    }
  }

  private loadFromDisk(): void {
    if (!this.persistencePath) return;
    try {
      const raw = fs.readFileSync(this.persistencePath, 'utf-8');
      const state = JSON.parse(raw) as EditorState;
      this.assets = ensureArray(state.assets);
      this.levels = ensureArray(state.levels);
      this.entities = ensureArray(state.entities);
      this.plan = state.plan;
    } catch (e) {
      // If loading fails, start fresh without throwing
      console.warn('EditorStore: failed to load persistence', e);
    }
  }

  private persistIfNeeded(): void {
    if (!this.persistencePath) return;
    try {
      const s = this._serializeState();
      fs.writeFileSync(this.persistencePath, JSON.stringify(s, null, 2), 'utf-8');
    } catch (e) {
      console.warn('EditorStore: failed to persist state', e);
    }
  }

  private _serializeState(): EditorState {
    return {
      assets: this.assets,
      levels: this.levels,
      entities: this.entities,
      plan: this.plan,
    };
  }

  public serialize(): EditorState {
    return this._serializeState();
  }

  public getState(): EditorState {
    return this._serializeState();
  }

  private nextId(): number {
    return ++this.lastId;
  }

  public upsertAsset(input: Partial<Asset>): Asset {
    let asset: Asset;
    if (input.id) {
      const idx = this.assets.findIndex((a) => a.id === input.id);
      if (idx >= 0) {
        asset = { ...this.assets[idx], ...input, updatedAt: nowIso() };
        this.assets[idx] = asset;
      } else {
        asset = {
          id: input.id,
          name: input.name ?? 'asset',
          type: input.type,
          data: input.data,
          updatedAt: nowIso(),
        };
        this.assets.push(asset);
      }
    } else {
      asset = {
        id: String(this.nextId()),
        name: input.name ?? 'asset',
        type: input.type,
        data: input.data,
        updatedAt: nowIso(),
      };
      this.assets.push(asset);
    }
    this.persistIfNeeded();
    return asset;
  }

  public upsertLevel(input: Partial<Level>): Level {
    let level: Level;
    if (input.id) {
      const idx = this.levels.findIndex((l) => l.id === input.id);
      if (idx >= 0) {
        level = { ...this.levels[idx], ...input, updatedAt: nowIso() };
        this.levels[idx] = level;
      } else {
        level = {
          id: input.id,
          name: input.name ?? 'level',
          description: input.description,
          data: input.data,
          updatedAt: nowIso(),
        };
        this.levels.push(level);
      }
    } else {
      level = {
        id: String(this.nextId()),
        name: input.name ?? 'level',
        description: input.description,
        data: input.data,
        updatedAt: nowIso(),
      };
      this.levels.push(level);
    }
    this.persistIfNeeded();
    return level;
  }

  public upsertEntity(input: Partial<EntityMeta>): EntityMeta {
    let entity: EntityMeta;
    if (input.id) {
      const idx = this.entities.findIndex((e) => e.id === input.id);
      if (idx >= 0) {
        entity = { ...this.entities[idx], ...input, updatedAt: nowIso() };
        this.entities[idx] = entity;
      } else {
        entity = {
          id: input.id,
          type: input.type ?? 'unknown',
          name: input.name,
          levelId: input.levelId,
          components: input.components,
          updatedAt: nowIso(),
        };
        this.entities.push(entity);
      }
    } else {
      entity = {
        id: String(this.nextId()),
        type: input.type ?? 'unknown',
        name: input.name,
        levelId: input.levelId,
        components: input.components,
        updatedAt: nowIso(),
      };
      this.entities.push(entity);
    }
    this.persistIfNeeded();
    return entity;
  }

  public upsertPlan(input: Partial<Plan>): Plan {
    const plan: Plan = {
      id: input.id ?? 'plan',
      name: input.name ?? 'plan',
      content: input.content ?? null,
      updatedAt: nowIso(),
    } as Plan;
    this.plan = plan;
    this.persistIfNeeded();
    return plan;
  }

  public getAssets(): Asset[] {
    return this.assets;
  }
  public getLevels(): Level[] {
    return this.levels;
  }
  public getEntities(): EntityMeta[] {
    return this.entities;
  }
  public getPlan(): Plan | undefined {
    return this.plan;
  }

  // utility to seed initial data (for tests/development)
  public seed(seedState: Partial<EditorState>): void {
    if (seedState.assets) this.assets = seedState.assets;
    if (seedState.levels) this.levels = seedState.levels;
    if (seedState.entities) this.entities = seedState.entities;
    if (seedState.plan) this.plan = seedState.plan as Plan;
  }
}

// Helper exports for tests to marshal/unmarshal JSON directly
export function marshalState(state: EditorState): string {
  return JSON.stringify(state, null, 2);
}

export function unmarshalState(json: string): EditorState {
  return JSON.parse(json) as EditorState;
}

// Factory to load from a file path easily in tests or runtime
export function createStoreWithPath(persistencePath?: string): EditorStore {
  const store = new EditorStore(persistencePath);
  return store;
}
