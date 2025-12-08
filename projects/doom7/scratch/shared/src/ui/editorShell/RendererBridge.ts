// Bridge between Engine and EditorShell to trigger redraws
import { Engine } from '../engine/engine';

export class RendererBridge {
  private engine: Engine | null = null;
  private onFrame: (() => void) | null = null;

  constructor(engine?: Engine) {
    if (engine) this.engine = engine;
  }

  setEngine(e: Engine) {
    this.engine = e;
  }

  onFrameTick(callback: () => void) {
    this.onFrame = callback;
  }

  // Exposed method; Engine will call to notify UI to redraw
  public notifyFrame() {
    if (this.onFrame) this.onFrame();
  }
}

export default RendererBridge;
