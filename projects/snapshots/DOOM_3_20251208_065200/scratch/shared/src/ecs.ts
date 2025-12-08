export type Entity = { id: string; name: string; x: number; y: number };
export type ECSAdapter = {
  registerEntity: (name: string) => string;
  getEntityPosition: (id: string) => { x: number; y: number } | null;
};

export class SimpleECS {
  private entities: Map<string, Entity> = new Map();

  constructor(private adapter: ECSAdapter) {}

  addEntity(name: string) {
    const id = this.adapter.registerEntity(name);
    this.entities.set(id, { id, name, x: 0, y: 0 });
    return id;
  }

  updatePosition(id: string, x: number, y: number) {
    const e = this.entities.get(id);
    if (!e) return;
    e.x = x; e.y = y;
  }

  getPosition(id: string) {
    const e = this.entities.get(id);
    if (!e) return null;
    return { x: e.x, y: e.y };
  }
}
