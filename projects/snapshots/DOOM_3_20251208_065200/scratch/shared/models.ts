export type PlayerState = {
  id: string;
  x: number;
  y: number;
  hp: number;
  facing: 'up'|'down'|'left'|'right';
};

export type LevelState = {
  id: string;
  name: string;
  width: number;
  height: number;
  tiles: string[][];
  players: Record<string, PlayerState>;
};

export type GameStore = {
  levels: Record<string, LevelState>;
};
