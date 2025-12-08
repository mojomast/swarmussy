// Example usage (could be wired into a small node script or browser demo)
import { RaycastRenderer } from './renderer_raycaster';
import { Engine } from './engine';
import { MapGrid, Player } from './types';

// Tiny demo map and player
const map: MapGrid = [
  [1,1,1,1,1],
  [1,0,0,0,1],
  [1,0,1,0,1],
  [1,0,0,0,1],
  [1,1,1,1,1],
];

const player: Player = {
  pos: { x: 2.5, y: 2.5 },
  dir: { x: -1, y: 0 },
  plane: { x: 0, y: 0.66 },
};

const renderer = new RaycastRenderer();
renderer.init(map, player);

const engine = new Engine();
engine.setRenderer(renderer);
engine.init(map, player);
engine.start();
