// Core data contracts for the in-engine grid editor and editors

export type TileType = 'empty' | 'wall' | 'floor' | 'water' | string;

export interface Weapon {
  id: string;
  name: string;
  damage: number;
  range: number;
}

export interface Monster {
  id: string;
  name: string;
  hp: number;
  attack: number;
}

export interface GridCell {
  row: number;
  col: number;
  value: TileType;
}
