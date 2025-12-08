export type TileType = 'empty' | 'wall' | 'floor' | 'water' | string;
export type GridCell = { r: number; c: number; value?: TileType };
export type Weapon = { id: string; name: string; damage: number; range?: number };
export type Monster = { id: string; name: string; hp: number; attack?: number };
