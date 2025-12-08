// Renderer interface for the 2.5D engine

import { MapGrid, Player } from './types';

export interface Renderer {
  // Initialize the renderer with the map and player
  init(map: MapGrid, player: Player): void;

  // Render a single frame; returns a simple image/array buffer representation for now
  renderFrame(): number[];
}
