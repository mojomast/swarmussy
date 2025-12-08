export interface EngineStateResponse {
  started: boolean;
  tick: number;
}

export type EngineStateEndpointPrototype = {
  endpoint: string;
  method: 'GET' | 'POST';
  description: string;
  response: EngineStateResponse;
};
