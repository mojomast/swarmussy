// Bridge between Engine.renderFrame() and editor canvas preview

export class EnginePreviewBridge {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D | null = null;
  private width: number = 320;
  private height: number = 200;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  private resize() {
    // maintain aspect ratio if canvas scaled by CSS; use the DOM size
    const rect = this.canvas.getBoundingClientRect();
    // use CSS pixels for internal buffer
    const w = Math.max(1, Math.floor(rect.width));
    const h = Math.max(1, Math.floor(rect.height));
    this.width = w; this.height = h;
    this.canvas.width = w; this.canvas.height = h;
  }

  public drawFrame(pixels: number[]) {
    if (!this.ctx) return;
    const w = this.canvas.width;
    const h = this.canvas.height;
    // assume pixels length = w*h; grayscale [0..255]
    const image = this.ctx.createImageData(w, h);
    for (let i = 0; i < w * h; i++) {
      const v = pixels[i] || 0;
      image.data[i * 4 + 0] = v; // r
      image.data[i * 4 + 1] = v; // g
      image.data[i * 4 + 2] = v; // b
      image.data[i * 4 + 3] = 255; // a
    }
    this.ctx.putImageData(image, 0, 0);
  }
}

export default EnginePreviewBridge;
