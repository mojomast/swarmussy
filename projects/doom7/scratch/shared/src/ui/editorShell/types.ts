export type Entity = {
  id: string;
  name: string;
  x: number;
  y: number;
  type: string;
  // additional optional fields
  [key: string]: any;
};

export type Level = {
  id: string;
  name: string;
  grid: number[][];
  entities: Entity[];
  assets: any[];
};

export type Asset = {
  id: string;
  name: string;
  type: string;
  data?: any;
};
