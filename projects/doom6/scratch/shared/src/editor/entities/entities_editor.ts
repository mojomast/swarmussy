// Editor helpers for mapping ECS entities to/from JSON representations
import { World } from '../../engine/core';

// Simple exporter: convert a list of entities into a JSON string-ish structure
export function exportEntities(entities: number[]): string {
  const data = entities.map((id) => ({ id }));
  return JSON.stringify(data, null, 2);
}

// Import entities from a JSON string and create them in the supplied world
export function importEntities(json: string, world: World): number[] {
  const arr = JSON.parse(json) as Array<any>;
  const created: number[] = [];
  if (!Array.isArray(arr)) return created;
  for (const item of arr) {
    const e = world.createEntity();
    created.push(e);
    // Attach a simple marker if provided
    if (typeof item?.type === 'string') {
      world.addComponent(e, { type: item.type });
    }
  }
  return created;
}

export default {};
