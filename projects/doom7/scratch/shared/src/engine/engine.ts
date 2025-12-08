// Core Engine scaffold: timing, loop control, and a pluggable renderer

import { MapGrid } from './types';
import { Renderer } from './renderer';
import { Player } from './types';
import { EventBus, CreateEventBus, RenderFrameEvent, HeartbeatEvent, createEventBus } from '../core/eventBus';

// TypeScript aliases for import compatibility if module resolution differs
type EB = EventBus;

export class Engine {
  private map: MapGrid | null = null;
  private player: Player | null = null;
  private renderer: Renderer | null = null;
  private lastTs: number = 0;
  private running: boolean = false;
  private fps: number = 60;
  private eventBus: EB;
  private lastHeartbeatMs: number = 0;

  constructor(eventBus?: EB) {
    this.eventBus = eventBus ?? createEventBus();
  }

  public setRenderer(r: Renderer) {
    this.renderer = r;
  }

  public init(map: MapGrid, player: Player) {
    this.map = map;
    this.player = player;
    // no-op additional init for now
  }

  public start() {
    if (!this.map || !this.player || !this.renderer) {
      throw new Error('Engine not fully initialized.');
    }
    // cross-platform timer
    this.lastTs = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
    this.running = true;
    const loop = (ts: number) => {
      if (!this.running) return;
      const now = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
      const dt = Math.min(64, now - this.lastTs); // clamp dt to avoid huge jumps
      this.lastTs = now;

      // publish a RenderFrame event for observers
      const rf: RenderFrameEvent = { type: 'RenderFrame', deltaMs: dt };
      try { this.eventBus.publish('RenderFrame', rf); } catch { /* no-op if no listeners */ }

      // Simple heartbeat to aid debugging / observability
      if (now - this.lastHeartbeatMs >= 1000) {
        const hb: HeartbeatEvent = { type: 'Heartbeat', timestamp: now };
        this.eventBus.publish('Heartbeat' as any, hb);
        this.lastHeartbeatMs = now;
        // lightweight log to indicate activity
        // eslint-disable-next-line no-console
        console.log(`Engine heartbeat @ ${Math.floor(now)} ms`);
      }

      // In a real engine, you'd update world state here using dt
      // For this scaffold, we simply render a frame through the Renderer interface
      this.renderer?.renderFrame();

      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  public stop() {
    this.running = false;
  }

  // Expose a simple render call to produce a frame for tests or UI previews
  public renderFrame(): number[] {
    if (!this.renderer) {
      throw new Error('Renderer not set on Engine.');
    }
    return this.renderer.renderFrame();
  }
}
