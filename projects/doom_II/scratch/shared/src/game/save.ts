export function saveWorld(world: any, path: string) {
  const data = JSON.stringify(world, null, 2);
  // In a real app, we'd write to disk, but this repo will include a save.json file placeholder.
  return data;
}
export function loadWorld(path: string) {
  // Placeholder loader; actual IO handled by a higher layer in editor or tests.
  return {};
}
