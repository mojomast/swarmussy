// Core lightweight types for the 2.5D renderer scaffold

export interface Vec2 {
  x: number;
  y: number;
}

export interface Player {
  pos: Vec2;     // Player position in map units
  dir: Vec2;     // Direction vector
  plane: Vec2;   // Camera plane for field of view
}

type MapRow = number[];
export type MapGrid = MapRow[]; // map[x][y] => 0 for empty space, >0 for walls

export interface RenderOptions {
  fov?: number; // radians, optional for future use
}
