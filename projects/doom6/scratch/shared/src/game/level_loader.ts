import { World } from '../engine/core';

// Load level JSON into the provided world. This MVP populates tiles as Positions and spawns a Player/Enemy.
export const loadLevelIntoWorld = (world: World, levelJson: any) => {
  if (!levelJson) return;
  // Spawn a simple player and enemy for MVP if specified
  if (Array.isArray(levelJson.entities)) {
    for (const ent of levelJson.entities) {
      const e = world.createEntity();
      if (ent.type === 'player') {
        world.addComponent(e, { name: 'Player' });
      } else if (ent.type === 'enemy') {
        world.addComponent(e, { name: 'Enemy' });
      }
    }
  }

  if (Array.isArray(levelJson.tiles)) {
    // create a position for each tile
    for (let i = 0; i < levelJson.tiles.length; i++) {
      for (let j = 0; j < levelJson.tiles[i].length; j++) {
        const tile = levelJson.tiles[i][j];
        if (tile !== 0) {
          const e = world.createEntity();
          world.addComponent(e, { Position: { x: i, y: j } });
        }
      }
    }
  }
};
