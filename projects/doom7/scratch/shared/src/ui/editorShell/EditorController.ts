// Lightweight editor controller for in-engine UI scaffold
import { Entity, Level, Asset } from './types';
import { Engine } from '../../engine/engine';
import { MapGrid } from '../../engine/types';

export type Panel = 'Levels' | 'Entities' | 'Assets' | 'Inspector';

export interface EditorState {
  level: Level;
  panel: Panel;
}

export class EditorController {
  state: EditorState;
  private engine?: Engine;

  constructor(initial?: Partial<Level>) {
    const defaultLevel: Level = {
      id: 'level-1',
      name: 'Untitled Level',
      grid: Array.from({ length: 12 }, () => Array.from({ length: 12 }, () => 0)),
      entities: [],
      assets: [],
    };
    this.state = {
      panel: 'Levels',
      level: { ...defaultLevel, ...initial },
    };
  }

  setEngine(e: Engine) {
    this.engine = e;
  }

  updatePreview(): number[] | null {
    if (this.engine) {
      // Return raw frame so UI can render; caller can decide where to route it
      return this.engine.renderFrame();
    }
    return null;
  }

  getPanel(): Panel {
    return this.state.panel;
  }

  setPanel(panel: Panel) {
    this.state.panel = panel;
  }

  getLevel(): Level {
    return this.state.level;
  }

  setLevel(level: Level) {
    this.state.level = level;
  }

  addEntity(e: Entity) {
    this.state.level.entities.push(e);
  }

  updateEntity(id: string, patch: Partial<Entity>) {
    const idx = this.state.level.entities.findIndex((e) => e.id === id);
    if (idx >= 0) {
      this.state.level.entities[idx] = { ...this.state.level.entities[idx], ...patch };
    }
  }

  removeEntity(id: string) {
    this.state.level.entities = this.state.level.entities.filter((e) => e.id !== id);
  }

  toJSON(): string {
    return JSON.stringify(this.state.level, null, 2);
  }

  loadFromJSON(text: string) {
    try {
      const parsed = JSON.parse(text);
      if (parsed && typeof parsed === 'object') {
        this.state.level = parsed as Level;
      }
    } catch {
      // no-op on error; leave current level
    }
  }
}

export default EditorController;
