// Lightweight in-process Event Bus with typed payloads

export type EventName = 'RenderFrame' | 'UserInput' | 'ContractUpdated' | 'Heartbeat';

// Event payload interfaces
export interface RenderFrameEvent {
  type: 'RenderFrame';
  deltaMs: number; // time since last frame in milliseconds
  frame?: number;
}

export interface UserInputEvent {
  type: 'UserInput';
  input: string; // e.g. 'MOVE_FORWARD', 'MOUSE_CLICK'
  details?: any;
}

export interface ContractUpdatedEvent {
  type: 'ContractUpdated';
  contractName: string; // e.g. 'EngineContract', 'EditorContract'
  version?: string;
}

export interface HeartbeatEvent {
  type: 'Heartbeat';
  timestamp: number;
  frame?: number;
}

// Centralized event map to enforce typing
export type EventPayloadMap = {
  RenderFrame: RenderFrameEvent;
  UserInput: UserInputEvent;
  ContractUpdated: ContractUpdatedEvent;
  Heartbeat: HeartbeatEvent;
};

export class EventBus {
  private listeners: {
    [K in keyof EventPayloadMap]?: Array<(payload: EventPayloadMap[K]) => void>;
  } = {};

  // Subscribe to a named event with a typed listener
  public subscribe<K extends keyof EventPayloadMap>(
    eventName: K,
    listener: (payload: EventPayloadMap[K]) => void
  ): void {
    if (!this.listeners[eventName]) this.listeners[eventName] = [];
    this.listeners[eventName]!.push(listener as any);
  }

  // Publish a typed event payload
  public publish<K extends keyof EventPayloadMap>(eventName: K, payload: EventPayloadMap[K]): void {
    const cbs = this.listeners[eventName];
    if (!cbs || cbs.length === 0) return;
    // Dispatch to all listeners
    for (const cb of cbs) {
      try {
        cb(payload);
      } catch (err) {
        // Log errors in listener execution to avoid breaking the loop
        // eslint-disable-next-line no-console
        console.error('EventBus listener error', err);
      }
    }
  }
}

// Convenience helper to easily create a bus instance
export function createEventBus(): EventBus {
  return new EventBus();
}

export default EventBus;
